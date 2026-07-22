"""Port for structured logging (SAD 8.5 - LogPort; SAD Cap. 24; ADR-0013).

AI Coding Standards Sec.12 forbids print(); every component must log
exclusively through this port, implemented by an infrastructure adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LogPort(ABC):
    """Contract implemented by infrastructure adapters responsible for
    recording application events, correlated by execution_id, module and
    workflow_step (SAD 24.5 - Estrutura da Mensagem).

    bind() lets a caller attach structured context once (e.g. execution_id,
    module, workflow_step) and reuse the returned LogPort for every
    subsequent call, instead of repeating the same fields on every log
    statement.
    """

    @abstractmethod
    def bind(self, **context: Any) -> "LogPort":
        """Return a new LogPort with context merged into its bound context."""
        raise NotImplementedError

    @abstractmethod
    def trace(self, message: str, **context: Any) -> None:
        raise NotImplementedError

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

    @abstractmethod
    def critical(self, message: str, **context: Any) -> None:
        raise NotImplementedError
