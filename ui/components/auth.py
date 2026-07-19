"""Basic operator authentication for the Streamlit UI.

The HITL approval page can execute real actions — it needs auth.
This is a simple password-based gate for internal/operator use.
"""

import os
import streamlit as st


def check_auth() -> bool:
    """Return True if the user is authenticated."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated


def login_form() -> None:
    """Render a simple login form."""
    st.markdown("## Operator Login")
    password = st.text_input("Password", type="password")
    expected = os.getenv("TS_OPERATOR_PASSWORD", "trustworthy-ai")

    if st.button("Login"):
        if password == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")


def require_auth() -> None:
    """Gate: if not authenticated, show login and stop."""
    if not check_auth():
        login_form()
        st.stop()
