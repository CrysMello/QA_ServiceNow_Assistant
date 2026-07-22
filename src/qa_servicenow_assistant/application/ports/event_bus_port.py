"""Port for the complementary Event Bus (SAD 8.5; ADR-0007; ADR-0012).

ADR-0012: o uso desta porta e restrito a preocupacoes transversais
(notificacoes internas, logging, telemetria, coleta de metricas) sem
dependencia funcional direta. Nunca deve ser usada para substituir uma
chamada direta que o Workflow Engine faca por outra Port.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from qa_servicenow_assistant.domain.events.domain_event import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class EventBusPort(ABC):
    """Contract implemented by infrastructure adapters that provide
    publish/subscribe dispatch for domain events."""

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Register handler to run whenever an event of exactly event_type
        is published."""
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Remove a previously registered handler. Safe to call even if the
        handler was never subscribed (no-op in that case)."""
        raise NotImplementedError

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Dispatch event synchronously to every handler subscribed to its
        exact type. Must never raise because a handler failed."""
        raise NotImplementedError
