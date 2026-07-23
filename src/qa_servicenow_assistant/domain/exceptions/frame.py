"""Frame resolution exceptions (SAD 18.6, 18.8).

Unlike Navigation Engine, Page Recognition and Selector Resolver - which
report "expected" failures as structured results instead of raising -
SAD 18.8 is explicit for Frame Resolver: "falhas devem ser propagadas por
excecoes padronizadas". This module follows that instruction literally,
even though it breaks the result-object pattern used elsewhere in this
codebase.
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class FrameError(QaServiceNowAssistantError):
    """Base exception for frame resolution failures."""


class FrameNotFoundError(FrameError):
    """Raised when: (a) no main frame is available and no criteria were
    given; or (b) a previously resolved frame descriptor no longer
    matches any live frame at handle-selection time (SAD 18.6 - "frame
    removido dinamicamente").

    Note (behavior confirmed in this correction): when frame_name or
    url_pattern is given to FrameResolutionEngine.resolve(), a frame that
    never appears no longer raises this exception immediately - the
    engine waits (condition-based, RNF-010) up to timeout_ms first, and
    raises FrameTimeoutError if nothing matches by then. FrameNotFoundError
    for that path would mean giving up without waiting at all, which is
    exactly what correction 2 removes.
    """


class AmbiguousFrameError(FrameError):
    """Raised when more than one frame matches the requested criteria."""


class FrameDetectionError(FrameError):
    """Raised when a Playwright infrastructure failure (not a "not
    found" or "timeout" outcome) occurs while listing frames or waiting
    for a matching frame to appear - e.g. the page/browser communication
    itself fails. Always chains the original Playwright exception via
    `raise ... from error`.
    """


class FrameAccessError(FrameError):
    """Raised when a Playwright infrastructure failure occurs while
    reading a live frame's properties or obtaining its handle during
    selection (select_frame). Always chains the original Playwright
    exception via `raise ... from error`.
    """


class FrameTimeoutError(FrameError):
    """Raised when waiting for a frame matching the requested criteria
    exceeds the configured timeout_ms (RNF-010 - sincronizacao baseada em
    condicoes, nao espera fixa). Never a silent fallback to the main
    frame: an explicit frame_name/url_pattern criterion that never
    matches always surfaces as this exception.
    """
