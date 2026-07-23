"""Logical identifier for a target page (SAD 8.4 - Value Objects)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageIdentifier:
    """Identifies a navigation target by a logical key.

    Deliberately minimal at this stage: just a name used to correlate
    navigation requests, history entries and logs. The real page-matching
    contract (URL/title/fingerprint/elements against the Knowledge Base)
    belongs to Page Recognition and Knowledge Manager (later modules);
    Navigation Engine only depends on an abstract NavigationValidationPort
    to decide whether a page matches a PageIdentifier.
    """

    key: str
