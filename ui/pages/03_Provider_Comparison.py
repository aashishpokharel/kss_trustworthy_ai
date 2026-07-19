"""Provider Comparison — Claude vs DeepSeek side-by-side metrics."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

st.set_page_config(page_title="Provider Comparison", page_icon="🔀", layout="wide")

st.title("🔀 Provider Comparison")
st.caption("Claude vs DeepSeek — eval, cost, latency side-by-side")

# --- Load provider config ---
from trust_safety.config import get_settings

settings = get_settings()

st.subheader("Configured Providers")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Anthropic / DeepSeek (Anthropic endpoint)")
    st.metric("Base URL", settings.anthropic_base_url or "https://api.anthropic.com")
    st.metric("Model", settings.anthropic_model)
    st.metric("Max Tokens", settings.anthropic_max_tokens)
    st.metric("Temperature", f"{settings.anthropic_temperature:.1f}")
    st.metric("Timeout", f"{settings.anthropic_timeout_seconds}s")
    st.metric("Cost Ceiling", f"${settings.anthropic_cost_ceiling_daily_usd}/day")
    st.metric("Zero Retention", "✅" if settings.anthropic_zero_retention else "⚠️ Not confirmed")
    st.metric("API Key", "✅ Configured" if settings.anthropic_api_key else "❌ Missing")

with col2:
    st.markdown("### DeepSeek (OpenAI-compatible endpoint)")
    st.metric("Base URL", settings.deepseek_base_url)
    st.metric("Model", settings.deepseek_model)
    st.metric("Max Tokens", settings.deepseek_max_tokens)
    st.metric("Temperature", f"{settings.deepseek_temperature:.1f}")
    st.metric("Timeout", f"{settings.deepseek_timeout_seconds}s")
    st.metric("Cost Ceiling", f"${settings.deepseek_cost_ceiling_daily_usd}/day")
    st.metric("Zero Retention", "✅" if settings.deepseek_zero_retention else "⚠️ Not confirmed")
    st.metric("API Key", "✅ Configured" if settings.deepseek_api_key else "❌ Missing")

# --- Environment Ladder ---
st.divider()
st.subheader("Environment Ladder")
ladder = settings.environment_ladder
rungs = ["mock", "sandbox", "shadow", "canary", "production"]
current_idx = rungs.index(ladder) if ladder in rungs else 0

cols = st.columns(5)
for i, rung in enumerate(rungs):
    with cols[i]:
        if i < current_idx:
            st.success(f"✅ {rung}")
        elif i == current_idx:
            st.info(f"📍 {rung} (current)")
        else:
            st.caption(f"⬜ {rung}")

st.metric("Canary Force HITL", "✅ Active" if settings.canary_force_hitl else "❌ Inactive")
st.metric("Routing Policy", settings.llm_routing_policy)

# --- Eval Results (placeholder — populated after real runs) ---
st.divider()
st.subheader("Eval Suite Results (per provider)")
st.info(
    "Run evaluations against live providers to populate this comparison. "
    "Use `POST /api/v1/eval/run` or the CI eval runner to generate results."
)

# Mock data for demonstration
import pandas as pd
demo_data = pd.DataFrame({
    "Metric": ["Injection Detection", "Benign Pass Rate", "Refusal Accuracy", "Groundedness Avg", "PII Detection"],
    "Anthropic": ["100%", "98%", "95%", "0.92", "100%"],
    "DeepSeek": ["—", "—", "—", "—", "—"],
})
st.dataframe(demo_data, width="stretch", hide_index=True)
st.caption("DeepSeek results pending — run the eval suite against the live endpoint.")
