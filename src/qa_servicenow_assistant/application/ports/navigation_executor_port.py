"""Port for the low-level navigation action (SAD 14.7: Navigation Engine
depends on Automation Engine to "executar mudancas de pagina").

Scope: only "go to this URL and wait for it to load". This is deliberately
narrower than the full future BrowserAutomationPort (click/fill/select
etc., SAD 13.4), which belongs to Automation Engine (a much later module)
and is not implemented here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class NavigationExecutorPort(ABC):
    """Contract implemented by infrastructure adapters that perform the
    actual browser navigation."""

    @abstractmethod
    def navigate(self, page: Any, url: str, timeout_ms: int) -> None:
        """Navigate page to url, waiting for the page to finish loading.

        Raises NavigationTimeoutError if the timeout is exceeded, or
        NavigationError for any other navigation failure.
        """
        raise NotImplementedError
