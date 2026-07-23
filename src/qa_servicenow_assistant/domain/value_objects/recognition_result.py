"""Outcome of a Page Recognition attempt (SAD Cap. 15)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.value_objects.recognition_confidence import (
    RecognitionConfidence,
)


@dataclass(frozen=True)
class RecognitionResult:
    """Immutable result of matching a BrowserSnapshot against known pages."""

    observed_url: str
    confidence: RecognitionConfidence
    matched_page: KnowledgePage | None = None
    matched_criteria: tuple[str, ...] = ()

    @property
    def is_recognized(self) -> bool:
        """SAD 15.5: only EXACT and PARTIAL count as recognized; LOW is
        explicitly "considerada nao reconhecida" and UNKNOWN has no match."""
        return self.confidence in (RecognitionConfidence.EXACT, RecognitionConfidence.PARTIAL)
