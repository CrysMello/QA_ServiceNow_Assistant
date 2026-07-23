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
    """Raised when no frame matches the requested criteria, or a
    previously resolved frame is no longer available (SAD 18.6 - "frame
    removido dinamicamente")."""


class AmbiguousFrameError(FrameError):
    """Raised when more than one frame matches the requested criteria."""
