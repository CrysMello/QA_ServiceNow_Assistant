"""Unit tests for SelectorResolver (SAD Cap. 17)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.services.selector_resolver import SelectorResolver
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)


def _snapshot(elements: tuple[CollectedElement, ...]) -> BrowserSnapshot:
    return BrowserSnapshot(url="https://dev.service-now.com", title="X", html="<html></html>", elements=elements)


def test_registered_selector_wins_over_everything_else() -> None:
    target = CollectedElement(
        tag_name="button",
        text="Submit",
        visible=True,
        attributes={"id": "submit-btn", "data_testid": "submit"},
    )
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot, registered_selector="kb-locator-42")

    assert result.selector.strategy == "knowledge_base"
    assert result.selector.value == "kb-locator-42"
    assert result.is_unique is True


def test_data_testid_preferred_over_id() -> None:
    target = CollectedElement(
        tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn", "data_testid": "submit"}
    )
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "data_testid"
    assert result.selector.value == '[data-testid="submit"]'


def test_id_preferred_over_aria() -> None:
    target = CollectedElement(
        tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn", "role": "button"}
    )
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "id"
    assert result.selector.value == "#submit-btn"


def test_aria_label_preferred_over_role() -> None:
    target = CollectedElement(
        tag_name="button",
        text="Submit",
        visible=True,
        attributes={"aria_label": "Submit form", "role": "button"},
    )
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "aria"
    assert result.selector.value == '[aria-label="Submit form"]'


def test_role_used_when_no_aria_label() -> None:
    target = CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"role": "button"})
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "aria"
    assert result.selector.value == '[role="button"]'


def test_css_name_used_when_no_id_or_aria() -> None:
    target = CollectedElement(tag_name="input", text="", visible=True, attributes={"name": "username"})
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "css"
    assert result.selector.value == 'input[name="username"]'


def test_text_used_as_last_resort() -> None:
    target = CollectedElement(tag_name="span", text="Welcome back", visible=True)
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.selector.strategy == "text"
    assert result.selector.value == 'text="Welcome back"'


def test_unresolvable_when_no_usable_attributes_or_text() -> None:
    target = CollectedElement(tag_name="div", text="", visible=True)
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.is_resolved is False
    assert result.selector is None
    assert result.considered == ()


def test_duplicate_id_is_not_unique_and_falls_back_to_next_candidate() -> None:
    target = CollectedElement(
        tag_name="button",
        text="Submit",
        visible=True,
        attributes={"id": "duplicate-id", "data_testid": "submit"},
    )
    sibling_with_same_id = CollectedElement(
        tag_name="button", text="Also Submit", visible=True, attributes={"id": "duplicate-id"}
    )
    snapshot = _snapshot((target, sibling_with_same_id))

    result = SelectorResolver().resolve(target, snapshot)

    # data_testid ("submit") is unique to target even though id is not
    assert result.selector.strategy == "data_testid"
    assert result.is_unique is True


def test_returns_best_effort_non_unique_selector_when_nothing_is_unique() -> None:
    target = CollectedElement(tag_name="div", text="Item", visible=True, attributes={"class": "row"})
    duplicate_text_sibling = CollectedElement(tag_name="div", text="Item", visible=True, attributes={"class": "row"})
    snapshot = _snapshot((target, duplicate_text_sibling))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.is_resolved is True
    assert result.is_unique is False
    assert result.selector.strategy == "text"  # only candidate available, still returned best-effort


def test_is_visible_reflects_target_visibility() -> None:
    target = CollectedElement(tag_name="button", text="Hidden", visible=False, attributes={"id": "hidden-btn"})
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    assert result.is_visible is False


def test_considered_lists_all_candidates_in_priority_order() -> None:
    target = CollectedElement(
        tag_name="button",
        text="Submit",
        visible=True,
        attributes={"id": "submit-btn", "data_testid": "submit", "aria_label": "Submit form"},
    )
    snapshot = _snapshot((target,))

    result = SelectorResolver().resolve(target, snapshot)

    strategies = [selector.strategy for selector in result.considered]
    assert strategies == ["data_testid", "id", "aria", "text"]
