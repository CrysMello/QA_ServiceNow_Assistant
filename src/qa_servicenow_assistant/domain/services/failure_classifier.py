"""FailureClassifier: pure domain service implementing SAD 19.2 ("classificar
falhas como transitorias ou permanentes") and SAD 19.6 (classification list).

Extensible by design (Open/Closed - AI Coding Standards): rather than a
hardcoded closed list of every exception type this project will ever
raise, this classifier holds a registry keyed by exception TYPE, walked
via the error's MRO so a more specific registration (e.g.
AmbiguousFrameError: PERMANENT) correctly overrides a broader one
registered on an ancestor (e.g. FrameError: TRANSIENT). Future modules
can register their own exception types via register() without modifying
this class.

Unknown/unregistered exception types default to PERMANENT: SAD 19.1
explicitly warns against "mascarar falhas permanentes", so an exception
this classifier has never been told about is treated conservatively -
not retried - rather than assumed safe to retry.
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.automation import AutomationError
from qa_servicenow_assistant.domain.exceptions.browser import (
    BrowserError,
    BrowserNotStartedError,
)
from qa_servicenow_assistant.domain.exceptions.frame import (
    AmbiguousFrameError,
    FrameError,
)
from qa_servicenow_assistant.domain.exceptions.navigation import NavigationError
from qa_servicenow_assistant.domain.value_objects.failure_classification import (
    FailureClassification,
)

_DEFAULT_CLASSIFICATIONS: dict[type[Exception], FailureClassification] = {
    # SAD 19.6 - "falha temporaria do navegador"
    BrowserError: FailureClassification.TRANSIENT,
    # Calling the browser before start() is a usage/programming error, not
    # a transient condition - retrying without fixing the caller is futile.
    BrowserNotStartedError: FailureClassification.PERMANENT,
    # SAD 19.6 - "timeout de carregamento", "perda momentanea de conectividade"
    NavigationError: FailureClassification.TRANSIENT,
    # SAD 18.6 failure modes (frame inexistente/inacessivel/timeout) mirror
    # SAD 19.6's "falha temporaria" category.
    FrameError: FailureClassification.TRANSIENT,
    # Ambiguity is a registration/data problem; retrying the same DOM will
    # not make it unambiguous.
    AmbiguousFrameError: FailureClassification.PERMANENT,
    # Automation Engine correction: ElementNotActionableError ("elemento
    # temporariamente indisponivel") and AutomationCommunicationError
    # ("perda momentanea de conectividade"/"falha temporaria do
    # navegador") are exactly the SAD 19.6 TRANSIENT examples quoted
    # above - covered here via the AutomationError base so an external
    # Retry Engine (Workflow Engine's, per step) actually retries them
    # instead of defaulting to PERMANENT as an unregistered type would.
    AutomationError: FailureClassification.TRANSIENT,
}


class FailureClassifier:
    """Classifies an exception instance as TRANSIENT or PERMANENT."""

    def __init__(self) -> None:
        self._classifications = dict(_DEFAULT_CLASSIFICATIONS)

    def register(
        self, exception_type: type[Exception], classification: FailureClassification
    ) -> None:
        """Register (or override) the classification for exception_type."""
        self._classifications[exception_type] = classification

    def classify(self, error: Exception) -> FailureClassification:
        for exception_type in type(error).__mro__:
            if exception_type in self._classifications:
                return self._classifications[exception_type]
        return FailureClassification.PERMANENT
