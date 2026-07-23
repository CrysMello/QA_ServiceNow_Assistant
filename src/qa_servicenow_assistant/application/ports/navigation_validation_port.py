"""Port for validating that a page matches the expected navigation target
(SAD 14.7: Navigation Engine depends on Page Recognition to "validar
identidade da pagina").

Scope: a single boolean match check. This is deliberately narrower than the
future Page Recognition module (SAD Cap. 15), which will use fingerprints,
confidence levels and the Knowledge Base - none of that is implemented
here. Until Page Recognition exists, callers must inject a suitable
adapter or test double.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class NavigationValidationPort(ABC):
    """Contract implemented by infrastructure/application adapters that
    confirm a page matches a PageIdentifier."""

    @abstractmethod
    def validate(self, page: Any, target: PageIdentifier) -> bool:
        """Return True if page currently matches target."""
        raise NotImplementedError
