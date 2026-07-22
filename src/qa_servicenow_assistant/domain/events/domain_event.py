"""Base type for domain events published on the complementary Event Bus.

ADR-0007 (InMemoryEventBus) and ADR-0012 (papel do Event Bus): o barramento
e um mecanismo complementar de infraestrutura para eventos transversais
(notificacoes internas, logging, telemetria, coleta de metricas) e nao
substitui as chamadas diretas do Workflow Engine via Ports & Adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    """Immutable base class for every event published on the Event Bus.

    Concrete events should subclass DomainEvent and add their own fields.
    Subscribers are matched by exact event type (see InMemoryEventBus).
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
