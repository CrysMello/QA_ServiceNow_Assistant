"""Unit tests for BrowserDataCollectedEvent."""

from __future__ import annotations

from qa_servicenow_assistant.domain.events.browser_data_collected_event import (
    BrowserDataCollectedEvent,
)
from qa_servicenow_assistant.domain.events.domain_event import DomainEvent


def test_defaults() -> None:
    event = BrowserDataCollectedEvent()

    assert event.url == ""
    assert event.title == ""
    assert event.element_count == 0


def test_is_a_domain_event() -> None:
    event = BrowserDataCollectedEvent(url="https://dev.service-now.com", element_count=3)

    assert isinstance(event, DomainEvent)
    assert event.url == "https://dev.service-now.com"
    assert event.element_count == 3
