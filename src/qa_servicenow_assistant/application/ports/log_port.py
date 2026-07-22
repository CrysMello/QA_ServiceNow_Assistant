"""Port for structured logging (SAD 8.5 - LogPort).

AI Coding Standards Sec.12 forbids print(); every component must log
exclusively through this port, implemented by an infrastructure adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LogPort(ABC):
    """Contract implemented by infrastructure adapters responsible for
    recording application events."""

    @abstractmethod
    def debug(self, message: str, **context: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def info(self, message: str, **context: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def warning(self, message: str, **context: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, message: str, **context: Any) -> None:
        raise NotImplementedError
