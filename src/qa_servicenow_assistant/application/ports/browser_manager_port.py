"""Port for browser lifecycle management (SAD 13.3 - Browser Session Manager).

Scope: launching/stopping the browser process and obtaining pages. This
port does NOT cover navigation (Navigation Engine), data collection
(Browser Data Collector) or executing test actions (Automation Engine) -
those are separate modules that will depend on this one.

The return type of new_page() is intentionally left as Any: per SAD 9.7
("A camada [Application] nao contem codigo especifico do Playwright"),
the abstract contract must not leak a Playwright-specific type. Concrete
adapters (infrastructure) return a real Playwright Page; callers that need
to act on it belong to infrastructure-level modules as well.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BrowserManagerPort(ABC):
    """Contract implemented by infrastructure adapters that manage the
    lifecycle of a browser instance."""

    @abstractmethod
    def start(self) -> None:
        """Launch the browser according to configuration.

        Idempotent: calling start() while already running must be a no-op.
        """
        raise NotImplementedError

    @abstractmethod
    def new_page(self) -> Any:
        """Create and return a new browser page.

        Raises BrowserNotStartedError if the browser has not been started.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Close all pages and the browser itself, releasing resources.

        Idempotent: calling stop() when not running must be a no-op.
        """
        raise NotImplementedError

    @abstractmethod
    def is_running(self) -> bool:
        """Return whether the browser is currently started."""
        raise NotImplementedError
