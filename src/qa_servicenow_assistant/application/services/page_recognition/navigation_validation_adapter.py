"""Adapts PageRecognitionEngine to NavigationValidationPort (SAD 15.7:
Page Recognition integra-se ao Navigation Engine para "validar a
navegacao realizada").

Lets Navigation Engine (Prompt 7) use real Page Recognition instead of a
test double, once a concrete KnowledgeRepository adapter exists (Knowledge
Manager, Prompt 18). Until then, callers still need to inject a
KnowledgeRepository test double or interim adapter into PageRecognitionEngine.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.browser_data_collector_port import (
    BrowserDataCollectorPort,
)
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.application.services.page_recognition.page_recognition_engine import (
    PageRecognitionEngine,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class PageRecognitionNavigationValidator(NavigationValidationPort):
    """NavigationValidationPort implementation backed by real Page
    Recognition: collects a BrowserSnapshot from the page (Browser Data
    Collector, Prompt 6), recognizes it, and checks whether the matched
    page's key equals the navigation target's key."""

    def __init__(
        self,
        page_recognition_engine: PageRecognitionEngine,
        browser_data_collector: BrowserDataCollectorPort,
    ) -> None:
        self._page_recognition_engine = page_recognition_engine
        self._browser_data_collector = browser_data_collector

    def validate(self, page: Any, target: PageIdentifier) -> bool:
        snapshot = self._browser_data_collector.collect(page)
        result = self._page_recognition_engine.recognize(snapshot)
        return (
            result.is_recognized
            and result.matched_page is not None
            and result.matched_page.key == target.key
        )
