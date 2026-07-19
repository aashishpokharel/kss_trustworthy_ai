"""
Trust & Safety Layer — FastAPI application entry point.

Start with::

    python -m trust_safety.main

Or::

    uvicorn trust_safety.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from trust_safety.config import Environment, get_settings
from trust_safety.gateway.dependencies import (
    _build_audit_logger,
    _build_tool_registry,
)
from trust_safety.gateway.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown logic."""
    # -- Startup --
    settings = get_settings()
    issues = settings.validate_rules()
    if issues:
        if settings.environment == Environment.PRODUCTION:
            raise RuntimeError(
                f"Configuration issues in production: {issues}"
            )
        else:
            import warnings
            for issue in issues:
                warnings.warn(f"Config issue: {issue}")

    # Pre-warm and verify the audit log
    logger = _build_audit_logger()
    report = logger.verify_integrity()
    if not report.valid and settings.environment != Environment.DEVELOPMENT:
        raise RuntimeError(
            f"Audit log integrity check failed: {report.errors}"
        )

    # Pre-warm the tool registry
    _build_tool_registry()

    yield  # -- app runs here --

    # -- Shutdown --
    # (file handles are closed via context manager, nothing to flush)


app = FastAPI(
    title="Trust & Safety Layer",
    description="Pipeline with checkpoints for safe LLM/Agent interactions.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


# ------------------------------------------------------------------
# Direct-run support
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "trust_safety.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
