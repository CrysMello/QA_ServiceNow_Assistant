"""Computes a structural fingerprint for a BrowserSnapshot (SAD 15.3).

KNOWN LIMITATION (read before relying on this for real matching): this is
QA ServiceNow Assistant's OWN fingerprint algorithm. The fingerprint
values actually stored in KnowledgePage.fingerprint are meant to be
produced externally by the ServiceNow Knowledge Builder, whose internal
algorithm is out of scope and unknown to this project (SRS 1.3 - "Fora do
Escopo: substituir o ServiceNow Knowledge Builder"). This placeholder is
deterministic and purely structural (sorted tag/id/data-testid markers),
but is NOT guaranteed to match Knowledge Builder's real fingerprints until
that algorithm is documented or reconciled. Matching degrades gracefully
when it does not: see PageRecognizer, where a fingerprint mismatch alone
does not force "unknown" if other criteria (URL/title/required elements)
still agree.
"""

from __future__ import annotations

import hashlib

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
)


def compute_fingerprint(snapshot: BrowserSnapshot) -> str:
    """Return a deterministic SHA-256 hex digest derived from the sorted
    set of (tag_name, id-or-data-testid) pairs among snapshot.elements."""
    markers = sorted(
        f"{element.tag_name}:{key}"
        for element in snapshot.elements
        if (key := element.attributes.get("id") or element.attributes.get("data_testid"))
    )
    digest_input = "|".join(markers).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()
