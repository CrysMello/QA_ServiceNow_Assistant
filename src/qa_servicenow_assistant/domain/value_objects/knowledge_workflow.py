"""KnowledgeWorkflow: a recorded flow catalogued by the Knowledge Base
(SAD 11.3 - "workflows.json ... Relacionar fluxos gravados").

Deliberately minimal: Workflow Engine (a later prompt, SAD Cap. 12) owns
the real execution model (Workflow/WorkflowStep/Transition/Precondition/
Postcondition/Execution Context, SAD 12.3/12.4) - this is only the
read-only catalog entry Knowledge Manager exposes, not an executable
workflow definition. step_keys is an ordered sequence of opaque
identifiers (page/element keys) a future Workflow Engine will interpret.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeWorkflow:
    key: str
    description: str
    step_keys: tuple[str, ...] = ()
