"""Governance Dashboard — metrics, trends, audit summary (read-only)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from trust_safety.governance.dashboard import MetricsCollector
from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from pathlib import Path

st.set_page_config(page_title="Governance Dashboard", page_icon="📊", layout="wide")

st.title("📊 Governance Dashboard")
st.caption("Trust & Safety Layer — real-time metrics from the audit log")

# --- Connect to audit log ---
@st.cache_resource
def get_collector():
    log_path = Path(os.getenv("TS_AUDIT_LOG_PATH", "./data/audit_log.jsonl"))
    store = AppendOnlyFileStore(log_path)
    logger = AuditLogger(store)
    return MetricsCollector(logger)

collector = get_collector()

# --- Time window ---
hours = st.sidebar.slider("Time window (hours)", 1, 168, 24)

# --- Fetch metrics ---
metrics = collector.get_metrics(hours=hours)
summary = collector.get_summary()

# --- KPI Row ---
st.subheader("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Interactions", metrics.total_interactions)
with col2:
    st.metric("Block Rate", f"{metrics.block_rate:.1%}")
with col3:
    st.metric("Injection Attempts", metrics.injection_attempts)
with col4:
    st.metric("Refusal Rate", f"{metrics.refusal_rate:.1%}")
with col5:
    st.metric("Groundedness Avg", f"{metrics.groundedness_avg:.2f}" if metrics.groundedness_samples > 0 else "N/A")

# --- Safety metrics ---
st.subheader("Safety")
col1, col2, col3 = st.columns(3)
with col1:
    from ui.components.metrics_charts import render_gauge
    block_pct = metrics.block_rate if metrics.total_interactions > 0 else 0
    render_gauge(1.0 - block_pct, "Pass Rate", max_val=1.0, threshold_warn=0.9)
with col2:
    render_gauge(metrics.groundedness_avg if metrics.groundedness_samples > 0 else 1.0,
                 "Groundedness", max_val=1.0, threshold_warn=0.8)
with col3:
    refusal_pct = 1.0 - metrics.refusal_rate if metrics.total_interactions > 0 else 1.0
    render_gauge(refusal_pct, "Non-Refusal Rate", max_val=1.0, threshold_warn=0.95)

# --- PII & Secrets ---
st.subheader("Data Privacy")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("PII Detections (Input)", metrics.pii_detections_input)
with col2:
    st.metric("PII Leaks (Output)", metrics.pii_leaks_output)
with col3:
    st.metric("Secrets Detected", metrics.secrets_detected)

# --- HITL ---
st.subheader("Human-in-the-Loop")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Approved", metrics.hitl_approved)
with col2:
    st.metric("Denied", metrics.hitl_denied)
with col3:
    st.metric("Timed Out", metrics.hitl_timed_out)
with col4:
    st.metric("Breaker Trips", metrics.breaker_trips)

# --- Audit Summary ---
st.subheader("Audit Log Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Entries", summary.total_entries)
with col2:
    st.metric("Integrity", "✅ Valid" if summary.integrity_valid else "❌ INVALID")
with col3:
    st.metric("First Entry", summary.first_entry_at.strftime("%Y-%m-%d %H:%M") if summary.first_entry_at else "N/A")

# --- Top event types ---
if summary.top_actions:
    from ui.components.metrics_charts import render_bar_chart
    labels = [a["event_type"] for a in summary.top_actions[:5]]
    values = [a["count"] for a in summary.top_actions[:5]]
    render_bar_chart(labels, values, "Top Event Types")

# --- Auto-refresh ---
st.sidebar.button("🔄 Refresh", on_click=st.rerun)
st.sidebar.caption(f"Last refresh: auto | Window: {hours}h")
