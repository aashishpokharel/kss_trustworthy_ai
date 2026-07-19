"""HITL Approval Queue — approve/reject high-risk tool calls (authenticated)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from datetime import datetime, timezone

from ui.components.auth import require_auth

st.set_page_config(page_title="HITL Approval Queue", page_icon="🛡️", layout="wide")

require_auth()

st.title("🛡️ HITL Approval Queue")
st.caption("Review and approve or deny high-risk tool calls")

# --- Connect to approval queue ---
@st.cache_resource
def get_queue():
    from trust_safety.orchestrator.approval_queue import ApprovalQueue
    from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
    from pathlib import Path
    log_path = Path(os.getenv("TS_AUDIT_LOG_PATH", "./data/audit_log.jsonl"))
    store = AppendOnlyFileStore(log_path)
    logger = AuditLogger(store)
    return ApprovalQueue(timeout_seconds=300, audit_logger=logger)

queue = get_queue()

# --- Stats ---
stats = queue.stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pending", stats["pending"])
with col2:
    st.metric("Approved", stats["approved"])
with col3:
    st.metric("Denied", stats["denied"])
with col4:
    st.metric("Timed Out", stats["timed_out"])

st.divider()

# --- Pending approvals ---
pending = queue.get_pending()

if not pending:
    st.success("No pending approvals. All clear! ✅")
else:
    st.subheader(f"Pending Requests ({len(pending)})")

    for req in pending:
        # Compute time remaining
        elapsed = (datetime.now(timezone.utc) - req.created_at).total_seconds()
        remaining = max(0, req.timeout_seconds - int(elapsed))
        urgent = remaining < 60

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {req.tool_name}")
                st.caption(f"Request ID: `{req.request_id}`")
                st.text(f"Params: {req.tool_params}")
                st.text(f"Requester: {req.requester} | Risk Tier: {req.risk_tier.value}")

            with col2:
                if urgent:
                    st.error(f"⏰ {remaining}s remaining!")
                else:
                    st.info(f"⏰ {remaining}s remaining")

                reviewer = st.text_input("Reviewer", value="operator", key=f"reviewer_{req.request_id}")
                reason = st.text_input("Reason", key=f"reason_{req.request_id}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Approve", key=f"approve_{req.request_id}", type="primary"):
                        queue.approve(req.request_id, reviewer)
                        st.rerun()
                with c2:
                    if st.button("❌ Deny", key=f"deny_{req.request_id}"):
                        queue.deny(req.request_id, reviewer, reason)
                        st.rerun()

st.sidebar.button("🔄 Refresh", on_click=st.rerun)
