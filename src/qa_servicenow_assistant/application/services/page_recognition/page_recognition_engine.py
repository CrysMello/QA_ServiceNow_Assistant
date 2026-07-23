"""Page Recognition Engine (SAD Cap. 15).

Orchestrates the recognition flow (SAD 15.4): query the Knowledge Base via
KnowledgeRepository, delegate matching to the pure PageRecognizer domain
service, and log the outcome (SAD 15.2 - "registrar inconsistencias de
reconhecimento").
"""

from __future__ import annotations

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.services.page_recognizer import PageRecognizer
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)
from qa_servicenow_assistant.domain.value_objects.recognition_result import (
    RecognitionResult,
)


class PageRecognitionEngine:
    """Recognizes the current page against the Knowledge Base."""

    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        log_port: LogPort,
        recognizer: PageRecognizer | None = None,
    ) -> None:
        self._knowledge_repository = knowledge_repository
        self._log_port = log_port
        self._recognizer = recognizer or PageRecognizer()

    def recognize(self, snapshot: BrowserSnapshot) -> RecognitionResult:
        known_pages = self._knowledge_repository.get_known_pages()
        result = self._recognizer.recognize(snapshot, known_pages)

        if result.is_recognized:
            self._log_port.info(
                "Page recognized",
                url=result.observed_url,
                matched_page=result.matched_page.key if result.matched_page else None,
                confidence=result.confidence.value,
                matched_criteria=result.matched_criteria,
            )
        else:
            self._log_port.warning(
                "Page not recognized",
                url=result.observed_url,
                confidence=result.confidence.value,
            )
        return result
