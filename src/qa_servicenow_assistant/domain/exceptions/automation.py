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
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class AutomationError(QaServiceNowAssistantError):
    """Base exception for Automation Engine action failures."""


class ElementNotActionableError(AutomationError):
    """Raised when Playwright's actionability wait for an element (being
    present, visible, enabled and stable) does not succeed within
    timeout_ms - covers SAD 13.6's "Elemento nao encontrado", "Elemento
    invisivel", "Elemento desabilitado" and "Timeout de carregamento",
    which Playwright's TimeoutError does not distinguish between. Always
    chains the original Playwright TimeoutError via `raise ... from
    error`.
    """


class AutomationCommunicationError(AutomationError):
    """Raised for any other Playwright failure during an action - covers
    SAD 13.6's "Perda da sessao do navegador", "Mudanca inesperada de
    pagina" and "Falha de comunicacao com o Playwright". Always chains
    the original Playwright Error via `raise ... from error`.
    """
