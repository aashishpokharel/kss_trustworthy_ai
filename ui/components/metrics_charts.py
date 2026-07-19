"""Chart components for the governance dashboard."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def render_gauge(value: float, title: str, max_val: float = 1.0, threshold_warn: float = 0.7) -> None:
    """Render a single gauge chart."""
    color = "green" if value >= threshold_warn else ("orange" if value >= 0.5 else "red")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={
            "axis": {"range": [0, max_val]},
            "bar": {"color": color},
            "threshold": {
                "line": {"color": "red", "width": 2},
                "thickness": 0.8,
                "value": threshold_warn * max_val,
            },
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, width="stretch")


def render_time_series(data: list[dict], x_key: str, y_key: str, title: str) -> None:
    """Render a line chart for time-series metrics."""
    if not data:
        st.info(f"No data for {title}")
        return

    import pandas as pd
    df = pd.DataFrame(data)
    fig = px.line(df, x=x_key, y=y_key, title=title)
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, width="stretch")


def render_bar_chart(labels: list[str], values: list[float], title: str) -> None:
    """Render a bar chart."""
    fig = go.Figure(go.Bar(x=labels, y=values))
    fig.update_layout(title=title, height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, width="stretch")
