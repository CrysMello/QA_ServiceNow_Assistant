"""Workflow (SAD 12.3 - "Workflow: Fluxo completo de execucao.
Representar um processo de negocio").

steps is an ordered, linear sequence: SAD 12.2 ("Controlar a ordem das
etapas") and 12.5 passo 5 ("Executar cada etapa sequencialmente") only
describe sequential execution - no branching/graph structure is
specified anywhere, so "Transition" (SAD 12.3 - "Mudanca de estado.
Definir o proximo passo") is implemented as "the next step in this
tuple", not a general state graph. This is a deliberate simplification,
documented as a known limitation rather than an invented, unspecified
branching model.
"""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep


@dataclass(frozen=True)
class Workflow:
    key: str
    description: str
    steps: tuple[WorkflowStep, ...]
