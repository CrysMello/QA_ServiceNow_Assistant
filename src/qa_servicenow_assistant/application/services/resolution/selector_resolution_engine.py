"""Selector Resolution Engine (SAD Cap. 17).

Thin orchestrator: delegates matching to the pure SelectorResolver domain
service and logs the outcome (SAD 17.7 - Log Engine: "registrar
diagnosticos"; SAD 17.2 - "registrar problemas de resolucao").
"""

from __future__ import annotations

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.services.selector_resolver import SelectorResolver
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.selector_resolution import (
    SelectorResolution,
)


class SelectorResolutionEngine:
    """Resolves the best locator for a target element and logs the result."""

    def __init__(self, log_port: LogPort, resolver: SelectorResolver | None = None) -> None:
        self._log_port = log_port
        self._resolver = resolver or SelectorResolver()

    def resolve(
        self,
        target: CollectedElement,
        snapshot: BrowserSnapshot,
        *,
        registered_selector: str | None = None,
    ) -> SelectorResolution:
        result = self._resolver.resolve(target, snapshot, registered_selector=registered_selector)

        if result.is_resolved and result.is_unique:
            self._log_port.debug(
                "Selector resolved",
                strategy=result.selector.strategy,
                value=result.selector.value,
                is_visible=result.is_visible,
            )
        elif result.is_resolved:
            self._log_port.warning(
                "Selector resolved but not confirmed unique in snapshot",
                strategy=result.selector.strategy,
                value=result.selector.value,
            )
        else:
            self._log_port.error(
                "Unable to resolve any selector for element",
                tag_name=target.tag_name,
            )
        return result
