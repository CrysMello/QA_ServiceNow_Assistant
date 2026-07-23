"""Knowledge Manager exceptions (SAD Cap. 11, 11.7 - Tratamento de Erros).

Unlike Navigation Engine, Page Recognition, Selector Resolver, Retry
Engine, Checkpoint Engine, Reporting Engine and Export Engine - which
report "expected" failures as structured results instead of raising -
SAD 11.7/11.8 use explicit, repeated directive language for Knowledge
Base LOADING failures: "Abortar inicializacao da base", "Interromper
carregamento", "Rejeitar a Base de Conhecimento". This module follows
that instruction literally for loading/initialization, the same
precedent as Frame Resolver's SAD-18.8-mandated exception propagation:
loading the Knowledge Base either succeeds completely or raises.

Single-item lookup misses (get_page/get_element/get_selector/
get_workflow/get_fingerprint not finding a key) are NOT modeled as
exceptions - SAD 11.7's "Elemento nao encontrado -> Retornar erro
controlado ao consumidor" is interpreted here as a plain `None` return
(the Python idiom for a controlled, non-crashing "not found", consistent
with dict.get() semantics), not a bespoke exception per accessor.
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class KnowledgeBaseError(QaServiceNowAssistantError):
    """Base exception for Knowledge Base loading failures."""


class KnowledgeBaseNotFoundError(KnowledgeBaseError):
    """Raised when the Knowledge Base directory or its manifest.json is
    missing (SAD 11.7 - "Manifest inexistente -> Abortar inicializacao
    da base")."""


class KnowledgeBaseFormatError(KnowledgeBaseError):
    """Raised when a present Knowledge Base file is not valid JSON or
    does not match the expected shape (SAD 11.7 - "JSON invalido ->
    Registrar erro e interromper carregamento"). Always chains the
    original error via `raise ... from error`.
    """


class IncompatibleKnowledgeBaseVersionError(KnowledgeBaseError):
    """Raised when manifest.version does not match the version this
    application supports (SAD 11.7 - "Versao incompativel -> Rejeitar a
    Base de Conhecimento"; SAD 11.8 - "Toda incompatibilidade de versao
    deve ser detectada durante a inicializacao")."""
