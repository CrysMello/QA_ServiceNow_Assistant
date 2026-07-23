"""FrameResolver: pure domain service implementing SAD 18.4 (passos 3-4)
and SAD 18.5 (Estrategias de Resolucao).

No I/O: operates only on already-detected FrameDescriptor facts (supplied
by FrameDetectorPort, an infrastructure concern) and does not touch
Playwright. frame_name/url_pattern stand in for "Frame registrado" (the
Knowledge Base source, SAD 18.5) the same way Selector Resolver's
registered_selector does - Knowledge Manager does not exist yet
(Prompt 18), so this is provisional (see confirmed decision on
Selector Resolver, applies equally here).

"Busca hierarquica" (SAD 18.5 - percorrer estruturas aninhadas de frames)
is handled for free: Playwright's page.frames already returns a flat list
including nested iframes, so no custom tree-walking is implemented here.
"""

from __future__ import annotations

from typing import Callable, Sequence

from qa_servicenow_assistant.domain.exceptions.frame import (
    AmbiguousFrameError,
    FrameNotFoundError,
)
from qa_servicenow_assistant.domain.value_objects.frame_descriptor import (
    FrameDescriptor,
)


class FrameResolver:
    """Selects a single FrameDescriptor among the frames currently
    available on a page, per SAD 18.5's strategies."""

    def resolve(
        self,
        frames: Sequence[FrameDescriptor],
        *,
        frame_name: str | None = None,
        url_pattern: str | None = None,
    ) -> FrameDescriptor:
        """frame_name takes precedence over url_pattern when both are
        given. With neither, the main frame is returned (SAD 18.5 -
        fallback). Raises FrameNotFoundError / AmbiguousFrameError -
        never returns None (SAD 18.8)."""
        if frame_name is not None:
            return self._select_unique(
                frames, "name", lambda frame: frame.name == frame_name, frame_name
            )

        if url_pattern is not None:
            return self._select_unique(
                frames, "url_pattern", lambda frame: url_pattern in frame.url, url_pattern
            )

        return self._select_main_frame(frames)

    def _select_main_frame(self, frames: Sequence[FrameDescriptor]) -> FrameDescriptor:
        main_frames = [frame for frame in frames if frame.is_main_frame]
        if not main_frames:
            raise FrameNotFoundError("No main frame available among the provided frames")
        return main_frames[0]

    def _select_unique(
        self,
        frames: Sequence[FrameDescriptor],
        criterion_name: str,
        predicate: Callable[[FrameDescriptor], bool],
        criterion_value: str,
    ) -> FrameDescriptor:
        matches = [frame for frame in frames if predicate(frame)]
        if not matches:
            raise FrameNotFoundError(f"No frame matches {criterion_name}={criterion_value!r}")
        if len(matches) > 1:
            labels = [frame.name or frame.url for frame in matches]
            raise AmbiguousFrameError(
                f"Multiple frames match {criterion_name}={criterion_value!r}: {labels}"
            )
        return matches[0]
