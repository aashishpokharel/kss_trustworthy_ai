"""
=======================
MODULE 2: DATA PRIVACY & RAG
=======================

=== USUAL WAY ===
documents = get_all_documents()
context = "\n".join(documents)
prompt = f"Answer based on: {context}"

=== TRUSTWORTHY WAY ===
- Access control per document
- PII redaction before embedding
- Data lineage tracking
- Right-to-forget support
- Permission checking on retrieval
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.safety import ContentFilter, AuditLogger, AuditEntry, compute_hash
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json


# ============================================================
# ANTI-PATTERN: RAG without Data Governance
# ============================================================

class UnsafeRAG:
    """
    === USUAL WAY: Ingest everything, no access control ===
    
    Risks:
    1. No PII detection in documents
    2. No access control - all users see all data
    3. No data lineage tracking
    4. Can't remove specific documents (right to forget)
    5. No audit trail for what data was used
    """
    
    def __init__(self):
        self.documents = []
        self.embeddings = {}
    
    def add_documents(self, documents: List[str]):
        """Add documents without any safety checks"""
        for doc in documents:
            self.documents.append(doc)
            # Embed and store (simplified)
            self.embeddings[len(self.documents) - 1] = f"embedding_of_{doc[:50]}"
    
    def retrieve(self, query: str, user_id: str = "anonymous") -> List[str]:
        """Retrieve documents without access control"""
        # No check on user permissions
        # No PII filtering
        # No audit trail
        return self.documents[:3]  # Return first 3 documents
    
    def generate(self, query: str, user_id: str = "anonymous") -> str:
        """Generate response using retrieved context"""
        context = self.retrieve(query, user_id)
        return f"Based on {len(context)} documents: {query[:50]}..."


# ============================================================
# TRUSTWORTHY PATTERN: RAG with Data Governance
# ============================================================

@dataclass
class Document:
    """Document with full metadata for governance"""
    id: str
    content: str
    sanitized_content: str = ""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_level: str = "public"  # public, internal, confidential, restricted
    allowed_users: List[str] = field(default_factory=list)
    pii_redacted: bool = False
    content_hash: str = ""
    
    def __post_init__(self):
        self.content_hash = compute_hash(self.content)


class TrustworthyRAG:
    """
    === TRUSTWORTHY WAY: Full data governance ===
    
    1. Scan all documents for PII before storing
    2. Enforce access control on retrieval
    3. Track data lineage
    4. Support document deletion (right to forget)
    5. Audit all accesses
    """
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.documents: Dict[str, Document] = {}
        self.audit_logger = audit_logger or AuditLogger()
        self.document_usage_log: List[Dict] = []
    
    def add_document(
        self,
        content: str,
        document_id: str,
        author: str = "",
        access_level: str = "public",
        allowed_users: Optional[List[str]] = None
    ) -> Dict:
        """
        Add document with safety processing and governance.
        
        Returns document metadata or error.
        """
        result = {
            "success": False,
            "document_id": document_id,
            "issues": [],
            "warnings": []
        }
        
        # Step 1: PII Detection
        pii_found = ContentFilter.detect_pii(content)
        if pii_found:
            result["warnings"].append(f"PII detected: {pii_found}")
        
        # Step 2: Sensitive content check
        has_sensitive, topics = ContentFilter.contains_sensitive_topic(content)
        if has_sensitive:
            result["warnings"].append(f"Sensitive topics: {topics}")
        
        # Step 3: Create sanitized version
        sanitized = ContentFilter.sanitize_pii(content)
        
        # Step 4: Store with metadata
        doc = Document(
            id=document_id,
            content=sanitized,  # Store sanitized version
            sanitized_content=sanitized,
            author=author,
            access_level=access_level,
            allowed_users=allowed_users or [],
            pii_redacted=len(pii_found) > 0
        )
        
        self.documents[document_id] = doc
        
        result["success"] = True
        result["document"] = {
            "id": doc.id,
            "content_length": len(doc.content),
            "access_level": doc.access_level,
            "pii_redacted": doc.pii_redacted,
            "content_hash": doc.content_hash
        }
        
        # Step 5: Audit the ingestion
        self._log_ingestion(document_id, author, result)
        
        return result
    
    def retrieve(
        self,
        query: str,
        user_id: str = "anonymous",
        user_roles: Optional[List[str]] = None
    ) -> Dict:
        """
        Retrieve documents with access control and audit.
        
        Returns filtered results based on user permissions.
        """
        result = {
            "success": True,
            "query": query,
            "user_id": user_id,
            "documents_retrieved": [],
            "documents_blocked": 0,
            "total_matches": 0,
            "warnings": []
        }
        
        user_roles = user_roles or ["public"]
        
        # Step 1: Scan query for injection
        from shared.safety import PromptInjectionDetector
        is_injection, patterns = PromptInjectionDetector.check(query)
        if is_injection:
            result["success"] = False
            result["error"] = "Query rejected: potential injection"
            return result
        
        # Step 2: Access-controlled retrieval
        for doc_id, doc in self.documents.items():
            if self._user_has_access(doc, user_id, user_roles):
                result["documents_retrieved"].append({
                    "id": doc.id,
                    "content_preview": doc.content[:200] if doc.content else "",
                    "access_level": doc.access_level,
                    "author": doc.author,
                    "pii_redacted": doc.pii_redacted
                })
            else:
                result["documents_blocked"] += 1
        
        result["total_matches"] = len(result["documents_retrieved"])
        
        # Step 3: Audit the access
        self._log_access(query, user_id, result)
        
        return result
    
    def _user_has_access(
        self,
        doc: Document,
        user_id: str,
        user_roles: List[str]
    ) -> bool:
        """Check if user has access to document"""
        
        # Public documents are accessible to everyone
        if doc.access_level == "public":
            return True
        
        # Internal documents accessible to any authenticated user
        if doc.access_level == "internal" and user_id != "anonymous":
            return True
        
        # Confidential documents need explicit permission
        if doc.access_level == "confidential":
            return user_id in doc.allowed_users
        
        # Restricted documents need specific role
        if doc.access_level == "restricted":
            return "admin" in user_roles or user_id in doc.allowed_users
        
        return False
    
    def delete_document(self, document_id: str, requester: str) -> Dict:
        """
        Delete a document (right to forget).
        
        === TRUSTWORTHY FEATURE ===
        Users can request deletion of their data.
        """
        result = {
            "success": False,
            "document_id": document_id,
            "action": "delete"
        }
        
        if document_id in self.documents:
            doc = self.documents[document_id]
            
            # Delete from storage
            del self.documents[document_id]
            
            result["success"] = True
            result["deleted_hash"] = doc.content_hash
            
            # Audit the deletion
            self._log_deletion(document_id, requester)
        
        return result
    
    def get_data_lineage(self, document_id: str) -> Dict:
        """
        Get full data lineage for a document.
        
        === TRUSTWORTHY FEATURE ===
        Trace where data came from, who accessed it, etc.
        """
        lineage = {
            "document_id": document_id,
            "exists": document_id in self.documents,
            "access_history": [],
            "modification_history": []
        }
        
        if document_id in self.documents:
            doc = self.documents[document_id]
            lineage["metadata"] = {
                "author": doc.author,
                "created_at": doc.created_at,
                "access_level": doc.access_level,
                "pii_redacted": doc.pii_redacted
            }
        
        # Gather access logs
        lineage["access_history"] = [
            log for log in self.document_usage_log
            if log.get("document_id") == document_id
        ]
        
        return lineage
    
    def _log_ingestion(self, document_id: str, author: str, details: Dict):
        """Log document ingestion"""
        entry = AuditEntry(
            user_id=author,
            request_hash=document_id,
            prompt_preview=f"Ingested document: {document_id}",
            response_preview=json.dumps(details)[:200],
            validation_passed=details["success"]
        )
        self.audit_logger.log(entry)
    
    def _log_access(self, query: str, user_id: str, details: Dict):
        """Log document access"""
        self.document_usage_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "query": query[:100],
            "documents_retrieved": details["total_matches"],
            "documents_blocked": details["documents_blocked"]
        })
    
    def _log_deletion(self, document_id: str, requester: str):
        """Log document deletion"""
        self.document_usage_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": requester,
            "action": "delete",
            "document_id": document_id
        })


# ============================================================
# DEMO
# ============================================================

def demo():
    """Demonstrate usual vs trustworthy RAG"""
    print("="*70)
    print("MODULE 2: DATA PRIVACY & RAG - USUAL vs TRUSTWORTHY")
    print("="*70)
    
    print("\n>> USUAL WAY: UnsafeRAG")
    unsafe_rag = UnsafeRAG()
    unsafe_rag.add_documents([
        "John Doe's SSN is 123-45-6789 and email is john@example.com",
        "Confidential: Q4 revenue projections $50M",
        "Internal memo about layoffs"
    ])
    
    # Any user can see all documents
    print(f"\n  Anonymous user retrieves: ")
    results = unsafe_rag.retrieve("revenue")
    print(f"  {results}")
    print(f"  RISK: PII and confidential data exposed to everyone!")
    
    print("\n>> TRUSTWORTHY WAY: TrustworthyRAG")
    audit_logger = AuditLogger()
    trustworthy_rag = TrustworthyRAG(audit_logger=audit_logger)
    
    # Add documents with proper governance
    docs_to_add = [
        {
            "content": "John Doe's SSN is 123-45-6789",
            "document_id": "doc1",
            "author": "admin",
            "access_level": "confidential",
            "allowed_users": ["admin", "hr_manager"]
        },
        {
            "content": "Machine learning is a subset of AI",
            "document_id": "doc2",
            "author": "researcher",
            "access_level": "public"
        }
    ]
    
    for doc_info in docs_to_add:
        result = trustworthy_rag.add_document(**doc_info)
        print(f"\n  Adding '{doc_info['document_id']}':")
        print(f"  Success: {result['success']}")
        if result.get('warnings'):
            print(f"  Warnings: {result['warnings']}")
        if result.get('document'):
            print(f"  Metadata: {result['document']}")
    
    # Access control demo
    print(f"\n  Anonymous user searches:")
    anon_result = trustworthy_rag.retrieve(
        "Tell me about John Doe",
        user_id="anonymous",
        user_roles=["public"]
    )
    print(f"  Documents accessible: {anon_result['total_matches']}")
    print(f"  Documents blocked: {anon_result['documents_blocked']}")
    
    print(f"\n  Admin user searches:")
    admin_result = trustworthy_rag.retrieve(
        "Tell me about John Doe",
        user_id="admin",
        user_roles=["admin"]
    )
    print(f"  Documents accessible: {admin_result['total_matches']}")
    print(f"  Documents blocked: {admin_result['documents_blocked']}")
    
    print(f"\n  Audit log entries: {len(audit_logger._entries)}")
    
    print(f"\n  Right to forget - deleting doc1:")
    delete_result = trustworthy_rag.delete_document("doc1", "admin")
    print(f"  Deleted: {delete_result['success']}")


if __name__ == "__main__":
    demo()