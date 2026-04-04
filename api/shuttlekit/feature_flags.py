"""
Deployment feature toggles from environment variables (api/.env).

Only whitelisted keys are exposed via GET /api/features — never echo arbitrary env names.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# When unset, chatbot stays on for backward compatibility with existing deployments.
_ENV_CHATBOT = "FEATURE_FLAGS_CHATBOT"

_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    key = raw.strip().lower()
    if key in _TRUE:
        return True
    if key in _FALSE:
        return False
    return default


def is_chatbot_enabled() -> bool:
    return env_bool(_ENV_CHATBOT, default=True)


def public_features_dict() -> dict[str, bool]:
    """Stable JSON shape for GET /api/features; keys are API-facing names only."""
    return {"chatbot": is_chatbot_enabled()}
