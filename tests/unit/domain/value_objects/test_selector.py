"""Unit tests for Selector / SelectorResolution."""

from __future__ import annotations

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector
from qa_servicenow_assistant.domain.value_objects.selector_resolution import (
    SelectorResolution,
)


def test_selector_holds_strategy_value_priority() -> None:
    selector = Selector(strategy="id", value="#submit-btn", priority=3)

    assert selector.strategy == "id"
    assert selector.value == "#submit-btn"
    assert selector.priority == 3


def test_is_resolved_true_when_selector_present() -> None:
    element = CollectedElement(tag_name="button", text="Submit", visible=True)
    resolution = SelectorResolution(
        target=element,
        selector=Selector(strategy="id", value="#submit-btn", priority=3),
        is_unique=True,
        is_visible=True,
    )

    assert resolution.is_resolved is True


def test_is_resolved_false_when_no_selector() -> None:
    element = CollectedElement(tag_name="div", text="", visible=True)
    resolution = SelectorResolution(target=element, selector=None, is_unique=False, is_visible=True)

    assert resolution.is_resolved is False


def test_considered_defaults_to_empty_tuple() -> None:
    element = CollectedElement(tag_name="div", text="", visible=True)
    resolution = SelectorResolution(target=element, selector=None, is_unique=False, is_visible=True)

    assert resolution.considered == ()
