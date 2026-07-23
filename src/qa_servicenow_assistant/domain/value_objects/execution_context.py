"""ExecutionContext: shared, mutable state passed to every step of a
single Workflow execution (SAD 12.3 - "Execution Context: Contexto
compartilhado. Armazenar informacoes da execucao").

Deliberately NOT a frozen dataclass - unlike every other domain value
object in this codebase (SAD 8.7 - "objetos de dominio devem ser
imutaveis sempre que possivel", emphasis on "sempre que possivel"): its
entire purpose is to accumulate information across sequential step
executions within one workflow run (e.g. a value fetched in step 1 that
step 3 needs). data is a plain dict for the same ergonomic-access reason
used elsewhere in this codebase (CollectedElement.attributes,
Checkpoint.temporary_data).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionContext:
    execution_id: str
    workflow_id: str
    data: dict[str, Any] = field(default_factory=dict)
