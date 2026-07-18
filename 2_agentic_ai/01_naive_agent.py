"""
=======================
MODULE 3a: NAIVE AGENT - ANTI-PATTERN
=======================

=== USUAL/NAIVE WAY ===
Build an AI agent that:
- Executes any tool without validation
- Trusts LLM output completely
- No permission boundaries
- No human-in-the-loop
- No sandboxing

This is what happens when engineers build agents quickly
without thinking about trustworthiness.

WARNING: This code demonstrates what NOT to do!
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Callable
import json
import subprocess
import os
import shutil


# ============================================================
# NAIVE AGENT - DO NOT USE IN PRODUCTION
# ============================================================

class NaiveAgent:
    """
    === ANTI-PATTERN: Everything wrong with AI Agents ===
    
    Problems:
    1. ❌ No input validation
    2. ❌ Executes arbitrary code from LLM
    3. ❌ No sandboxing
    4. ❌ No human approval
    5. ❌ Can delete/modify files
    6. ❌ No audit trail
    7. ❌ Can access any system resource
    8. ❌ No conversation boundaries
    """
    
    def __init__(self):
        self.conversation_history = []
        
        # Tools available to the agent - NO SAFETY CHECKS
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "execute_command": self._tool_execute_command,
            "delete_file": self._tool_delete_file,
            "search_web": self._tool_search_web,
            "send_email": self._tool_send_email,
            "access_database": self._tool_access_database,
        }
    
    def process_message(self, user_message: str) -> str:
        """
        Process user message and execute tools.
        
        DANGER: LLM decides which tools to call and with what args!
        """
        print(f"\n[NAIVE AGENT] Received: {user_message}")
        
        # No input validation - could contain injection
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # LLM decides which tools to call
        # In a real scenario, this would call an actual LLM
        # Here we simulate tools being called
        tool_calls = self._simulate_llm_tool_selection(user_message)
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})
            
            print(f"  [NAIVE] LLM decided to call: {tool_name}({tool_args})")
            
            if tool_name in self.tools:
                try:
                    # Execute tool WITHOUT any safety checks!
                    result = self.tools[tool_name](**tool_args)
                    print(f"  [NAIVE] Result: {str(result)[:100]}")
                    self.conversation_history.append({
                        "role": "assistant",
                        "tool": tool_name,
                        "result": str(result)
                    })
                except Exception as e:
                    print(f"  [NAIVE] Error: {e}")
        
        # LLM generates final response (simulated)
        response = self._simulate_llm_response(user_message)
        return response
    
    def _simulate_llm_tool_selection(self, message: str) -> List[Dict]:
        """
        Simulate LLM deciding which tools to call.
        
        In a real attack, the LLM could be manipulated via
        prompt injection to call dangerous tools.
        """
        message_lower = message.lower()
        
        # The LLM might be tricked into calling dangerous tools
        if "delete" in message_lower and "file" in message_lower:
            # DANGER: LLM might extract paths from user input
            return [
                {"tool": "delete_file", "args": {"path": message_lower.split("delete")[1].strip()}}
            ]
        
        if "run" in message_lower or "execute" in message_lower:
            return [
                {"tool": "execute_command", "args": {"command": message_lower.replace("run", "").replace("execute", "").strip()}}
            ]
        
        if "read" in message_lower:
            # Extract filename from message (vulnerable to path traversal)
            import re
            files = re.findall(r'\b\w+\.\w+\b', message)
            return [{"tool": "read_file", "args": {"path": f}} for f in files]
        
        if "email" in message_lower:
            import re
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', message)
            return [{"tool": "send_email", "args": {"to": e, "subject": "Test", "body": "Hello"}} for e in emails]
        
        return [{"tool": "read_file", "args": {"path": "/etc/passwd"}}]
    
    def _simulate_llm_response(self, message: str) -> str:
        """Simulate LLM response"""
        return f"I've processed your request. I called {len(self.conversation_history)} tools."
    
    # ============================================================
    # UNSAFE TOOL IMPLEMENTATIONS
    # ============================================================
    
    def _tool_read_file(self, path: str) -> str:
        """
        DANGER: No path validation - can read any file!
        """
        with open(path, 'r') as f:
            return f.read()
    
    def _tool_write_file(self, path: str, content: str) -> str:
        """
        DANGER: Can overwrite any file!
        """
        with open(path, 'w') as f:
            f.write(content)
        return f"Written to {path}"
    
    def _tool_execute_command(self, command: str) -> str:
        """
        DANGER: Executes arbitrary system commands!
        """
        result = subprocess.run(
            command,
            shell=True,  # DANGER: shell=True allows command chaining
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
    
    def _tool_delete_file(self, path: str) -> str:
        """
        DANGER: Can delete any file!
        """
        if os.path.exists(path):
            os.remove(path)
            return f"Deleted: {path}"
        return f"File not found: {path}"
    
    def _tool_search_web(self, query: str) -> str:
        """
        DANGER: No rate limiting, no content filtering!
        """
        # Simulated web search
        return f"Search results for: {query}"
    
    def _tool_send_email(self, to: str, subject: str, body: str) -> str:
        """
        DANGER: Can send emails to anyone!
        """
        return f"Email sent to {to}: {subject}"
    
    def _tool_access_database(self, query: str) -> str:
        """
        DANGER: SQL injection possible!
        """
        return f"Database results for: {query}"


# ============================================================
# DEMO THE DANGERS
# ============================================================

def demo():
    """Demonstrate why naive agents are dangerous"""
    print("="*70)
    print("WARNING: NAIVE AGENT - ANTI-PATTERN DEMO")
    print("="*70)
    
    agent = NaiveAgent()
    
    # Test Case 1: Prompt Injection
    print("\n" + "="*40)
    print("TEST 1: Prompt Injection Attack")
    print("="*40)
    print("\nUser says: 'Run this command: /etc/passwd'")
    print("Agent interprets as: Execute command 'this command:'")
    # This would try to execute a dangerous command
    
    # Test Case 2: File Deletion
    print("\n" + "="*40)
    print("TEST 2: File Deletion Attack")
    print("="*40)
    print("\nUser says: 'delete all important files'")
    agent.process_message("delete all important files")
    
    # Test Case 3: Data Extraction
    print("\n" + "="*40)
    print("TEST 3: Data Extraction")
    print("="*40)
    print("\nUser says: 'read config.json, secrets.env, and database.yml'")
    agent.process_message("read config.json, secrets.env, and database.yml")
    
    # Test Case 4: Email Spam
    print("\n" + "="*40)
    print("TEST 4: Email Abuse")
    print("="*40)
    print("\nUser says: 'send email to everyone@company.com'")
    agent.process_message("send email to everyone@company.com")
    
    print("\n" + "!"*70)
    print("NAIVE AGENT PROBLEMS:")
    print("!"*70)
    print("""
    1. ❌ NO TOOL SAFETY - Any tool can be called with any arguments
    2. ❌ NO PERMISSION SYSTEM - No concept of user roles
    3. ❌ NO HUMAN APPROVAL - Automated decisions without oversight
    4. ❌ NO INPUT VALIDATION - Prompt injection works
    5. ❌ NO SANDBOXING - Can access entire filesystem
    6. ❌ NO RATE LIMITING - Can send 1000s of emails
    7. ❌ NO AUDIT TRAIL - Cannot trace what happened
    8. ❌ NO OUTPUT VALIDATION - LLM output trusted blindly
    9. ❌ shell=True ON COMMANDS - Allows command chaining
    10. ❌ NO PATH VALIDATION - Path traversal vulnerabilities
    """)


if __name__ == "__main__":
    demo()