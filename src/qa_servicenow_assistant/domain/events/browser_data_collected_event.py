"""Event published after a browser data collection (ADR-0012).

This is a lightweight, complementary notification (url/title/element
count) for cross-cutting concerns (logging, telemetry, audit) - it is
deliberately NOT the mechanism by which the collected BrowserSnapshot
reaches its functional consumers (e.g. a future Page Recognition module).
That is a direct return value from BrowserDataCollectorPort.collect(),
per ADR-0012 ("nunca deve ser usada para substituir uma chamada direta").
"""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class BrowserDataCollectedEvent(DomainEvent):
    url: str = ""
    title: str = ""
    element_count: int = 0
