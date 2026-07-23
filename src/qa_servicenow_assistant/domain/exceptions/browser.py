"""Browser lifecycle exceptions (SAD 13.3 - Browser Session Manager)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class BrowserError(QaServiceNowAssistantError):
    """Base exception for browser lifecycle failures."""


class BrowserLaunchError(BrowserError):
    """Raised when the browser process fails to launch."""


class BrowserNotStartedError(BrowserError):
    """Raised when an operation requires a running browser that was not
    started (or was already stopped)."""


class BrowserDataCollectionError(BrowserError):
    """Raised when collecting URL/DOM/element data from a page fails."""
