"""In-memory synchronous implementation of EventBusPort (ADR-0007).

ADR-0012: este barramento e infraestrutura complementar, nao o mecanismo
primario de orquestracao (que permanece o Workflow Engine, via chamadas
diretas por Ports & Adapters). O despacho e sincrono e em processo; nao ha
persistencia, entrega entre processos ou retentativa.
"""

from __future__ import annotations

from collections import defaultdict

from qa_servicenow_assistant.application.ports.event_bus_port import (
    EventBusPort,
    EventHandler,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.events.domain_event import DomainEvent


class InMemoryEventBus(EventBusPort):
    """Synchronous, in-process publish/subscribe dispatcher.

    LogPort e obrigatorio (nao opcional): uma falha em um subscriber deve
    sempre ser registrada (AI Development Guide - "nao ocultar excecoes"),
    mas sem jamais propagar de volta para quem publicou o evento - isolar
    falhas de handler e exatamente o motivo de existir um barramento para
    preocupacoes transversais (ADR-0012).
    """

    def __init__(self, log_port: LogPort) -> None:
        self._log_port = log_port
        self._handlers: defaultdict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def publish(self, event: DomainEvent) -> None:
        event_type = type(event)
        handlers = tuple(self._handlers.get(event_type, ()))
        self._log_port.debug(
            "Publishing domain event",
            event_type=event_type.__name__,
            subscriber_count=len(handlers),
        )
        for handler in handlers:
            self._invoke_handler(handler, event)

    def _invoke_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        # Fronteira deliberada e restrita de isolamento de excecoes: o
        # ADR-0012 exige que o Event Bus nunca afete o fluxo principal
        # orquestrado pelo Workflow Engine. Um unico subscriber com defeito
        # nao pode quebrar publish() para os demais nem propagar para quem
        # publicou. Esta e a unica excecao justificada, neste codigo, a
        # regra do AI Coding Standards Sec.11 ("nunca utilizar except
        # generico"); a falha nunca e descartada silenciosamente - e
        # sempre registrada com contexto completo via LogPort.
        try:
            handler(event)
        except Exception as error:  # noqa: BLE001 - fronteira de isolamento intencional
            self._log_port.error(
                "Event handler raised an exception",
                event_type=type(event).__name__,
                handler=getattr(handler, "__qualname__", repr(handler)),
                error=str(error),
            )
