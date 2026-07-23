"""PageRecognizer: pure domain service implementing SAD 15.4 (passos 3-5)
and SAD 15.5 (Estrategia de Correspondencia).

No I/O: does not query the Knowledge Base itself (that is
KnowledgeRepository's job - an application-layer port, called by
PageRecognitionEngine before invoking this service) and does not touch
Playwright. Per SAD 15.8 ("nenhuma regra de negocio deve ser implementada
neste componente"), this only compares already-loaded data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.services.page_fingerprint import (
    compute_fingerprint,
)
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)
from qa_servicenow_assistant.domain.value_objects.recognition_confidence import (
    RecognitionConfidence,
)
from qa_servicenow_assistant.domain.value_objects.recognition_result import (
    RecognitionResult,
)

# SAD 15.5 describes four qualitative tiers without numeric thresholds;
# these ratios are QA ServiceNow Assistant's own chosen mapping and may be
# revisited once real-world Knowledge Base data is available.
_EXACT_RATIO = 1.0
_PARTIAL_RATIO = 0.5


@dataclass(frozen=True)
class _CriterionScore:
    applicable: int
    matched: int
    matched_criteria: tuple[str, ...]

    def ratio(self) -> float:
        return self.matched / self.applicable if self.applicable else 0.0


_NO_MATCH_SCORE = _CriterionScore(applicable=0, matched=0, matched_criteria=())


class PageRecognizer:
    """Matches a BrowserSnapshot against a list of known KnowledgePage
    entries and returns the best RecognitionResult."""

    def recognize(
        self, snapshot: BrowserSnapshot, known_pages: Sequence[KnowledgePage]
    ) -> RecognitionResult:
        best_page: KnowledgePage | None = None
        best_score = _NO_MATCH_SCORE

        for page in known_pages:
            score = self._score(snapshot, page)
            # Tie-break by absolute matched count: two candidates can share
            # the same ratio (e.g. 1/1 vs 2/2), and the one with more
            # corroborating criteria is the stronger, more specific match.
            if (score.ratio(), score.matched) > (best_score.ratio(), best_score.matched):
                best_page = page
                best_score = score

        confidence = self._classify(best_score)
        # SAD 15.5: LOW is explicitly "considerada nao reconhecida", so only
        # EXACT and PARTIAL carry a matched_page forward.
        matched_page = (
            best_page
            if confidence in (RecognitionConfidence.EXACT, RecognitionConfidence.PARTIAL)
            else None
        )

        return RecognitionResult(
            observed_url=snapshot.url,
            confidence=confidence,
            matched_page=matched_page,
            matched_criteria=best_score.matched_criteria,
        )

    def _score(self, snapshot: BrowserSnapshot, page: KnowledgePage) -> _CriterionScore:
        matched_criteria: list[str] = []
        applicable = 0
        matched = 0

        applicable += 1
        if page.url_pattern in snapshot.url:
            matched += 1
            matched_criteria.append("url")

        if page.title is not None:
            applicable += 1
            if page.title == snapshot.title:
                matched += 1
                matched_criteria.append("title")

        if page.fingerprint is not None:
            applicable += 1
            if page.fingerprint == compute_fingerprint(snapshot):
                matched += 1
                matched_criteria.append("fingerprint")

        if page.required_element_keys:
            applicable += 1
            if self._has_all_required_elements(snapshot, page.required_element_keys):
                matched += 1
                matched_criteria.append("required_elements")

        return _CriterionScore(
            applicable=applicable, matched=matched, matched_criteria=tuple(matched_criteria)
        )

    def _has_all_required_elements(
        self, snapshot: BrowserSnapshot, required_keys: tuple[str, ...]
    ) -> bool:
        observed_keys = {
            key
            for element in snapshot.elements
            if (key := element.attributes.get("id") or element.attributes.get("data_testid"))
        }
        return all(required_key in observed_keys for required_key in required_keys)

    def _classify(self, score: _CriterionScore) -> RecognitionConfidence:
        ratio = score.ratio()
        if score.applicable == 0 or ratio == 0.0:
            return RecognitionConfidence.UNKNOWN
        if ratio >= _EXACT_RATIO:
            return RecognitionConfidence.EXACT
        if ratio >= _PARTIAL_RATIO:
            return RecognitionConfidence.PARTIAL
        return RecognitionConfidence.LOW
