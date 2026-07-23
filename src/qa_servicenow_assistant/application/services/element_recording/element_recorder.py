"""Element Recorder (Module Specifications Cap. 8).

Keeps an in-memory, chronological journal of elements observed during
execution, for later use by traceability-oriented modules (Reporting
Engine, Screenshot Engine - both later prompts). Contains no
selection/resolution logic (that is Selector Analyzer/Resolver, later
prompts) and produces no Knowledge Base artifact (see RecordedElement
docstring for the scope boundary).

Isolation between executions: records are all kept in a single internal
list, but every record carries a mandatory execution_id (RNF-011), and
records_for_execution() lets callers retrieve only their own execution's
recordings. A composition root should still create a fresh ElementRecorder
per execution when possible (to bound memory growth over a long-lived
process); records_for_execution() is the safety net if an instance ends
up reused across executions regardless.
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
    """Records CollectedElement observations tagged with execution
    context and a label."""

    def __init__(self, log_port: LogPort) -> None:
        self._log_port = log_port
        self._records: list[RecordedElement] = []

    @property
    def records(self) -> tuple[RecordedElement, ...]:
        """All recordings so far, oldest first, across every execution_id
        seen by this instance. Prefer records_for_execution() when you
        only want a single execution's recordings (see class docstring -
        isolation)."""
        return tuple(self._records)

    def record(
        self,
        element: CollectedElement,
        *,
        execution_id: str,
        label: str,
        page_url: str,
        page_id: str | None = None,
    ) -> RecordedElement:
        """Record a single element observation and return the record."""
        recorded = RecordedElement(
            element=element,
            execution_id=execution_id,
            label=label,
            page_url=page_url,
            page_id=page_id,
        )
        self._records.append(recorded)
        self._log_port.debug(
            "Element recorded",
            execution_id=execution_id,
            label=label,
            tag_name=element.tag_name,
            element_id=recorded.element_id,
            page_url=page_url,
            page_id=page_id,
        )
        return recorded

    def record_many(
        self,
        elements: Iterable[CollectedElement],
        *,
        execution_id: str,
        label: str,
        page_url: str,
        page_id: str | None = None,
    ) -> tuple[RecordedElement, ...]:
        """Record several elements sharing the same execution/label/page context."""
        return tuple(
            self.record(
                element,
                execution_id=execution_id,
                label=label,
                page_url=page_url,
                page_id=page_id,
            )
            for element in elements
        )

    def records_for_execution(self, execution_id: str) -> tuple[RecordedElement, ...]:
        """All recordings for a single execution_id, oldest first. This is
        the isolation mechanism between executions (see class docstring)."""
        return tuple(record for record in self._records if record.execution_id == execution_id)

    def records_for_label(self, label: str) -> tuple[RecordedElement, ...]:
        """All recordings matching a given label, oldest first, across
        every execution_id seen by this instance."""
        return tuple(record for record in self._records if record.label == label)
