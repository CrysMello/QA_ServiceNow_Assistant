"""Navigation execution exceptions (SAD Cap. 14).

Note: a target page failing validation is NOT modeled as an exception - it
is a normal, expected outcome represented by NavigationResult(success=False,
...), so callers (future Workflow Engine / Retry Engine) can inspect and
decide policy without exception-based control flow. These exceptions are
reserved for actual execution failures (timeout, browser/navigation crash).
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class NavigationError(QaServiceNowAssistantError):
    """Base exception for navigation execution failures."""


class NavigationTimeoutError(NavigationError):
    """Raised when navigating to a URL exceeds the configured timeout."""
