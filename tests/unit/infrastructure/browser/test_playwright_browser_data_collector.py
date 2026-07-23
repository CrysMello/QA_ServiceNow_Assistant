"""Unit tests for PlaywrightBrowserDataCollector, using a fake page so the
Python-side mapping/wiring logic is tested independently of real Playwright
JS evaluation (covered separately by the integration test).
"""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError

from qa_servicenow_assistant.application.ports.event_bus_port import EventBusPort
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.events.browser_data_collected_event import (
    BrowserDataCollectedEvent,
)
from qa_servicenow_assistant.domain.events.domain_event import DomainEvent
from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserDataCollectionError,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_data_collector import (
    PlaywrightBrowserDataCollector,
)


class FakePage:
    def __init__(
        self,
        url: str = "https://dev.service-now.com/home",
        title: str = "Home",
        html: str = "<html></html>",
        evaluate_result: list[dict[str, Any]] | None = None,
        evaluate_error: Exception | None = None,
    ) -> None:
        self.url = url
        self._title = title
        self._html = html
        self._evaluate_result = evaluate_result if evaluate_result is not None else []
        self._evaluate_error = evaluate_error
        self.evaluate_calls: list[tuple[str, Any]] = []

    def title(self) -> str:
        return self._title

    def content(self) -> str:
        return self._html

    def evaluate(self, script: str, arg: Any = None) -> list[dict[str, Any]]:
        self.evaluate_calls.append((script, arg))
        if self._evaluate_error is not None:
            raise self._evaluate_error
        return self._evaluate_result


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeEventBus(EventBusPort):
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def subscribe(self, event_type: type[DomainEvent], handler: Any) -> None:
        pass

    def unsubscribe(self, event_type: type[DomainEvent], handler: Any) -> None:
        pass

    def publish(self, event: DomainEvent) -> None:
        self.published.append(event)


_RAW_ELEMENT = {
    "tagName": "button",
    "text": "Submit",
    "visible": True,
    "attributes": {
        "id": "submit-btn",
        "class": "",
        "name": "",
        "type": "",
        "role": "",
        "aria_label": "",
        "data_testid": "submit",
    },
}


def test_collect_returns_snapshot_with_page_facts() -> None:
    page = FakePage(url="https://dev.service-now.com/x", title="X", html="<p>x</p>")
    log_port = FakeLogPort()
    event_bus = FakeEventBus()
    collector = PlaywrightBrowserDataCollector(log_port, event_bus)

    snapshot = collector.collect(page)

    assert snapshot.url == "https://dev.service-now.com/x"
    assert snapshot.title == "X"
    assert snapshot.html == "<p>x</p>"


def test_collect_maps_raw_elements_to_collected_elements() -> None:
    page = FakePage(evaluate_result=[_RAW_ELEMENT])
    collector = PlaywrightBrowserDataCollector(FakeLogPort(), FakeEventBus())

    snapshot = collector.collect(page)

    assert len(snapshot.elements) == 1
    element = snapshot.elements[0]
    assert element.tag_name == "button"
    assert element.text == "Submit"
    assert element.visible is True
    assert element.attributes["id"] == "submit-btn"
    assert element.attributes["data_testid"] == "submit"


def test_collect_caps_elements_defensively_in_python(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_elements = [_RAW_ELEMENT] * 10
    page = FakePage(evaluate_result=raw_elements)
    collector = PlaywrightBrowserDataCollector(FakeLogPort(), FakeEventBus(), max_elements=3)

    snapshot = collector.collect(page)

    assert len(snapshot.elements) == 3


def test_collect_publishes_summary_event() -> None:
    page = FakePage(
        url="https://dev.service-now.com/y",
        title="Y",
        evaluate_result=[_RAW_ELEMENT, _RAW_ELEMENT],
    )
    event_bus = FakeEventBus()
    collector = PlaywrightBrowserDataCollector(FakeLogPort(), event_bus)

    collector.collect(page)

    assert len(event_bus.published) == 1
    published = event_bus.published[0]
    assert isinstance(published, BrowserDataCollectedEvent)
    assert published.url == "https://dev.service-now.com/y"
    assert published.title == "Y"
    assert published.element_count == 2


def test_collect_logs_debug_summary() -> None:
    page = FakePage()
    log_port = FakeLogPort()
    collector = PlaywrightBrowserDataCollector(log_port, FakeEventBus())

    collector.collect(page)

    assert len(log_port.debug_calls) == 1
    message, context = log_port.debug_calls[0]
    assert "collected" in message.lower()
    assert context["url"] == page.url


def test_collect_wraps_playwright_error() -> None:
    page = FakePage(evaluate_error=PlaywrightError("page crashed"))
    collector = PlaywrightBrowserDataCollector(FakeLogPort(), FakeEventBus())

    with pytest.raises(BrowserDataCollectionError, match="page crashed"):
        collector.collect(page)
