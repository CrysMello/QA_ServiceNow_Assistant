"""Port for executing UI actions against an already-resolved locator
(SAD Cap. 13, 13.4 - Operacoes Suportadas).

page is typed Any because it accepts either a Playwright Page or a
Frame (both expose a compatible .locator() API) - selecting the correct
one is Frame Resolver's job (SAD 13.8 - "Toda interacao deve ocorrer
dentro do contexto correto de pagina e frame"), which happens upstream,
before a caller reaches Automation Engine.

selector is an already-resolved Selector (SAD 13.2 - "Consumir locators
resolvidos pelo Selector Resolver") - this port never decides WHICH
element to target, only acts on selector.value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from qa_servicenow_assistant.domain.value_objects.selector import Selector


class AutomationExecutorPort(ABC):
    """Contract implemented by infrastructure adapters that perform real
    UI actions. Every method raises ElementNotActionableError or
    AutomationCommunicationError on failure (SAD 13.8) - never a bare
    exception (AI Coding Standards Sec.11)."""

    @abstractmethod
    def click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def double_click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def fill(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def select_option(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def check(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def uncheck(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def upload_file(self, page: Any, selector: Selector, file_path: str, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def press_key(self, page: Any, selector: Selector, key: str, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def hover(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait_for(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        raise NotImplementedError
