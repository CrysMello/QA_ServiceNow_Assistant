"""WorkflowStep (SAD 12.3 - "Workflow Step: Etapa individual. Executar
uma atividade especifica"; "Precondition: Condicao de entrada. Validar
requisitos da etapa"; "Postcondition: Condicao de saida. Validar
conclusao da etapa").

action/preconditions/postconditions are caller-supplied callables, the
same design already used by RetryEngine's `operation: Callable[[], T]`:
Workflow Engine "nao implementa acoes especificas do Playwright" (SAD
12.8) and does not know what a step actually DOES - callers (future
Automation Engine, or today's already-existing Navigation Engine/Page
Recognition/Selector Resolver) compose steps by wrapping their own calls.
This keeps Workflow Engine free of business rules and reusable for any
workflow (SAD 12.8 - "Cada workflow deve possuir responsabilidade unica";
"Novos workflows devem ser adicionados sem alterar os existentes").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)


@dataclass(frozen=True)
class WorkflowStep:
    key: str
    description: str
    action: Callable[[ExecutionContext], Any]
    preconditions: tuple[Callable[[ExecutionContext], bool], ...] = ()
    postconditions: tuple[Callable[[ExecutionContext], bool], ...] = ()
