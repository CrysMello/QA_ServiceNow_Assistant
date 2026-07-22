"""Masks sensitive data before it reaches any log sink.

Enforces RNF-001 (SRS - Seguranca) and AI Coding Standards Sec.17: senhas,
tokens, cookies, headers de autorizacao e demais dados sensiveis nunca
podem ser gravados em logs ou relatorios.
"""

from __future__ import annotations

from typing import Any

MASK_PLACEHOLDER = "***MASKED***"

_SENSITIVE_KEY_MARKERS: tuple[str, ...] = (
    "password",
    "senha",
    "token",
    "secret",
    "cookie",
    "authorization",
    "api_key",
    "apikey",
    "credential",
    "credencial",
)


def mask_sensitive_data(value: Any) -> Any:
    """Return a copy of value with sensitive fields replaced by a placeholder.

    dict keys are matched case-insensitively as substrings against
    _SENSITIVE_KEY_MARKERS (e.g. "auth_token", "Authorization" and
    "COOKIE_VALUE" all match). Lists and tuples are masked element by
    element, recursively. Any other type is returned unchanged.
    """
    if isinstance(value, dict):
        return {key: _mask_value(key, item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_sensitive_data(item) for item in value)
    return value


def _mask_value(key: Any, value: Any) -> Any:
    if _is_sensitive_key(key):
        return MASK_PLACEHOLDER
    return mask_sensitive_data(value)


def _is_sensitive_key(key: Any) -> bool:
    normalized_key = str(key).lower()
    return any(marker in normalized_key for marker in _SENSITIVE_KEY_MARKERS)
