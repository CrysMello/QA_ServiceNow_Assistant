"""FrameDescriptor: technology-agnostic description of a browser frame
(SAD Cap. 18 - Frame Resolver)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameDescriptor:
    """Identifies a single frame (main page or iframe) by name and URL,
    without leaking a Playwright Frame type into domain/application
    contracts (SAD 9.7)."""

    name: str
    url: str
    is_main_frame: bool
