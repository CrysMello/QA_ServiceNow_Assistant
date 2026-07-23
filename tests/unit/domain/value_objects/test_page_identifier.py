"""Unit tests for PageIdentifier."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


def test_holds_key() -> None:
    identifier = PageIdentifier(key="test_plan_list")

    assert identifier.key == "test_plan_list"


def test_is_immutable() -> None:
    identifier = PageIdentifier(key="test_plan_list")

    with pytest.raises(FrozenInstanceError):
        identifier.key = "other"  # type: ignore[misc]


def test_equal_by_value() -> None:
    assert PageIdentifier(key="a") == PageIdentifier(key="a")
    assert PageIdentifier(key="a") != PageIdentifier(key="b")
