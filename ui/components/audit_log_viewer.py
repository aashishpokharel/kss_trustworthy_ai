"""Audit log table component with filtering."""

import streamlit as st
import pandas as pd
from datetime import datetime


def render_audit_log(entries: list, max_rows: int = 50) -> None:
    """Render a filterable audit log table."""
    if not entries:
        st.info("No audit entries to display.")
        return

    st.subheader("Audit Log")

    col1, col2 = st.columns(2)
    with col1:
        event_filter = st.selectbox(
            "Event type",
            ["all"] + sorted(set(e.event_type for e in entries if e.event_type)),
            key="audit_event_filter",
        )
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["all", "allowed", "blocked", "flagged"],
            key="audit_status_filter",
        )

    filtered = entries
    if event_filter != "all":
        filtered = [e for e in filtered if e.event_type == event_filter]
    if status_filter != "all":
        filtered = [e for e in filtered if e.status == status_filter]

    rows = []
    for e in filtered[-max_rows:]:
        rows.append({
            "Timestamp": e.timestamp.strftime("%H:%M:%S") if e.timestamp else "",
            "Event": e.event_type,
            "Action": e.action[:60] if e.action else "",
            "Status": e.status,
            "Risk": f"{e.risk_score:.2f}" if e.risk_score else "-",
            "User": e.user_id or "-",
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No matching entries.")
