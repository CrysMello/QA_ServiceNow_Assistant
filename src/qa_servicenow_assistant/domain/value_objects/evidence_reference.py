"""Reference to a piece of evidence attached to an execution report
(SAD 22.4 - "Evidencias: Capturas de tela e anexos"; SAD 22.6 -
"Screenshot Engine: Anexar evidencias").

Screenshot Engine (SAD Cap. 23) does not exist yet (a later prompt) - this
is a narrow, provisional DTO capturing only what Reporting Engine itself
needs to reference evidence in a report, the same precedent used for
NavigationValidationPort (defined before Page Recognition existed) and
EvidenceReference's sibling records elsewhere in this codebase. Screenshot
Engine is expected to produce values shaped like this (or a superset of
it) once implemented.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceReference:
    """description: what the evidence shows (e.g. "before_submit",
    "validation_failure"). path: where the evidence file is stored,
    caller-supplied; Reporting Engine does not read or validate the file
    itself, only records the reference (SAD 22.8 - "As evidencias devem
    manter vinculo com a execucao correspondente")."""

    description: str
    path: str
