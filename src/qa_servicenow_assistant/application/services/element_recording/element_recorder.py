"""Element Recorder (Module Specifications Cap. 8).

Keeps an in-memory, chronological journal of elements observed during the
current execution, for later use by traceability-oriented modules
(Reporting Engine, Screenshot Engine - both later prompts). Contains no
selection/resolution logic (that is Selector Analyzer/Resolver, later
prompts) and produces no Knowledge Base artifact (see RecordedElement
docstring for the scope boundary).
"""

from __future__ import annotations

from typing import Iterable

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.recorded_element import (
    RecordedElement,
)


class ElementRecorder:
    """Records CollectedElement observations tagged with a label."""

    def __init__(self, log_port: LogPort) -> None:
        self._log_port = log_port
        self._records: list[RecordedElement] = []

    @property
    def records(self) -> tuple[RecordedElement, ...]:
        """All recordings so far, oldest first."""
        return tuple(self._records)

    def record(self, element: CollectedElement, *, label: str, page_url: str) -> RecordedElement:
        """Record a single element observation and return the record."""
        recorded = RecordedElement(element=element, label=label, page_url=page_url)
        self._records.append(recorded)
        self._log_port.debug(
            "Element recorded",
            label=label,
            tag_name=element.tag_name,
            page_url=page_url,
        )
        return recorded

    def record_many(
        self, elements: Iterable[CollectedElement], *, label: str, page_url: str
    ) -> tuple[RecordedElement, ...]:
        """Record several elements sharing the same label and page_url."""
        return tuple(
            self.record(element, label=label, page_url=page_url) for element in elements
        )

    def records_for_label(self, label: str) -> tuple[RecordedElement, ...]:
        """All recordings matching a given label, oldest first."""
        return tuple(record for record in self._records if record.label == label)
