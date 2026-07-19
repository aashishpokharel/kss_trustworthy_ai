"""Trust & Safety Layer — Operator UI entry point.

Streamlit auto-discovers pages from the ui/pages/ directory.
This file is the Home page.  Use the sidebar to navigate.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

st.set_page_config(
    page_title="Trust & Safety Layer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("🛡️ Trust & Safety")
st.sidebar.caption("Operator Console")
st.sidebar.divider()
st.sidebar.caption("Version: 0.1.0")
st.sidebar.caption("Phase 6 — LLM Integration")

# --- Home page content ---
st.title("🛡️ Trust & Safety Layer")
st.subheader("Operator Console")
st.markdown("""
This is the internal operator UI for the Trust & Safety Layer.

### Pages (use sidebar to navigate)
- **📊 Dashboard** — Real-time governance metrics, safety KPIs, audit summary
- **🛡️ HITL Approval Queue** — Review and approve/deny high-risk tool calls (authenticated)
- **🔀 Provider Comparison** — Claude vs DeepSeek configuration and eval results

### Quick Actions
- Start the API server: `uvicorn trust_safety.main:app --port 8000`
- Run eval suite: `POST /api/v1/eval/run`
- Check health: `GET /api/v1/health`
- View API docs: `http://localhost:8000/docs`
""")

# Quick stats
from trust_safety.config import get_settings
settings = get_settings()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Environment", settings.environment.value)
with col2:
    st.metric("LLM Provider", settings.llm_provider)
with col3:
    st.metric("Ladder Rung", settings.environment_ladder)
with col4:
    st.metric("HITL Timeout", f"{settings.hitl_timeout_seconds}s")
