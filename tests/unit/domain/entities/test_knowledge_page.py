"""Unit tests for the KnowledgePage entity."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage


def test_defaults() -> None:
    page = KnowledgePage(key="home", url_pattern="/home")

    assert page.title is None
    assert page.fingerprint is None
    assert page.required_element_keys == ()
    assert page.metadata == {}


def test_is_immutable() -> None:
    page = KnowledgePage(key="home", url_pattern="/home")

    with pytest.raises(FrozenInstanceError):
        page.key = "other"  # type: ignore[misc]
