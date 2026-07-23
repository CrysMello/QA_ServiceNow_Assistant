"""Port for persisting generated report content (SAD 22.3 - "Report
Generator" output persistence; SAD 22.6 - "Configuration Manager: Obter
formato e diretorios")."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ReportRepositoryPort(ABC):
    """Contract implemented by infrastructure adapters responsible for
    writing rendered report content to storage. Raises
    ReportPersistenceError on I/O failure - never a bare exception
    (AI Coding Standards Sec.11)."""

    @abstractmethod
    def save(self, content: str, file_name: str) -> Path:
        """Persist content under file_name and return the full path
        written to."""
        raise NotImplementedError
