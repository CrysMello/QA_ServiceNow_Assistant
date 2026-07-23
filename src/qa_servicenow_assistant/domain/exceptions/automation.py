"""Automation Engine exceptions (SAD Cap. 13).

SAD 13.8 is explicit for Automation Engine, the same as Frame Resolver
(SAD 18.8): "Erros devem ser propagados como excecoes de aplicacao
padronizadas". This module follows that instruction literally - it
raises, it never returns a "failed" structured result.

SAD 13.6 lists seven failure situations: "Elemento nao encontrado",
"Elemento invisivel", "Elemento desabilitado", "Timeout de carregamento",
"Perda da sessao do navegador", "Mudanca inesperada de pagina", "Falha de
comunicacao com o Playwright". Empirically verified (sandboxed Playwright
calls, same discipline used for Frame Resolver): Playwright's sync API
does not expose seven distinguishable exception types for these - a
Locator action raises exactly ONE of two exception classes:
TimeoutError (a subclass of Error) when its internal actionability wait
(present + visible + enabled + stable) does not succeed in time - which
is indistinguishable, from the caller's side, between "not found",
"invisible", "disabled" or "generic timeout" - and the base Error for
everything else (closed page/context/browser, navigation lost, and any
other communication failure). Rather than inventing false precision this
codebase cannot actually deliver, the first four SAD 13.6 rows are
consolidated into ElementNotActionableError and the remaining three into
AutomationCommunicationError.

FailureClassifier registration (post-Prompt 20 correction review):
AutomationError itself is deliberately left UNREGISTERED, so any
subclass (including future ones) defaults to PERMANENT via the
classifier's own safe fallback (SAD 19.1 - "mascarar falhas
permanentes"), consistent with how the rest of this codebase's exception
hierarchies are classified (e.g. BrowserNotStartedError,
AmbiguousFrameError). Only ElementNotActionableError is registered
TRANSIENT explicitly - it is the one case genuinely matching SAD 19.6's
"elemento temporariamente indisponivel"/"timeout de carregamento".
AutomationCommunicationError is NOT registered TRANSIENT: it bundles
genuinely permanent causes (malformed selector, wrong element type for
the operation) together with possibly-transient ones (lost session,
communication hiccup) that Playwright's generic Error class does not let
us tell apart without fragile message-text parsing - the safer,
conservative default (PERMANENT) applies until/unless this bucket is
later split using a reliable signal. InvalidUploadFileError is also
deliberately unregistered/PERMANENT: a missing path or nonexistent file
will never be fixed by retrying the same call.
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class AutomationError(QaServiceNowAssistantError):
    """Base exception for Automation Engine action failures. Deliberately
    unregistered in FailureClassifier - see module docstring."""


class ElementNotActionableError(AutomationError):
    """Raised when Playwright's actionability wait for an element (being
    present, visible, enabled and stable) does not succeed within
    timeout_ms - covers SAD 13.6's "Elemento nao encontrado", "Elemento
    invisivel", "Elemento desabilitado" and "Timeout de carregamento",
    which Playwright's TimeoutError does not distinguish between. Always
    chains the original Playwright TimeoutError via `raise ... from
    error`. Registered TRANSIENT in FailureClassifier.
    """


class AutomationCommunicationError(AutomationError):
    """Raised for any other Playwright failure during an action - covers
    SAD 13.6's "Perda da sessao do navegador", "Mudanca inesperada de
    pagina" and "Falha de comunicacao com o Playwright", but also
    genuinely permanent causes (malformed selector, wrong element type)
    that Playwright reports through the same generic Error class. Always
    chains the original Playwright Error via `raise ... from error`. NOT
    registered in FailureClassifier - defaults to PERMANENT (see module
    docstring for the rationale).
    """


class InvalidUploadFileError(AutomationError):
    """Raised by upload_file BEFORE any Playwright call when file_path
    (or any entry of a sequence of paths) is missing, empty, or does not
    point to an existing file. Never chains a Playwright error - this is
    caught purely by local validation. NOT registered in
    FailureClassifier - defaults to PERMANENT: a missing/nonexistent
    file is never fixed by retrying the same call.
    """
