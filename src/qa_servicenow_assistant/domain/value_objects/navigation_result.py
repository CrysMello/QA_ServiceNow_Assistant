"""Outcome of a single navigation attempt (SAD Cap. 14)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


@dataclass(frozen=True)
class NavigationResult:
    """Immutable record of one navigate() call, kept in Navigation Engine's
    in-memory history (SAD 14.3 - History Manager)."""

    target: PageIdentifier
    url: str
    success: bool
    duration_ms: float
    error_message: str | None = None
