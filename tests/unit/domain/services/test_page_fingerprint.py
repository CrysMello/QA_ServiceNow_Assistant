"""Unit tests for compute_fingerprint."""

from __future__ import annotations

from qa_servicenow_assistant.domain.services.page_fingerprint import (
    compute_fingerprint,
)
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)


def _snapshot(elements: tuple[CollectedElement, ...]) -> BrowserSnapshot:
    return BrowserSnapshot(url="https://dev.service-now.com", title="X", html="<html></html>", elements=elements)


def test_deterministic_for_same_elements() -> None:
    elements = (CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn"}),)

    first = compute_fingerprint(_snapshot(elements))
    second = compute_fingerprint(_snapshot(elements))

    assert first == second


def test_order_independent() -> None:
    button = CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn"})
    input_el = CollectedElement(tag_name="input", text="", visible=True, attributes={"id": "username"})

    fingerprint_a = compute_fingerprint(_snapshot((button, input_el)))
    fingerprint_b = compute_fingerprint(_snapshot((input_el, button)))

    assert fingerprint_a == fingerprint_b


def test_different_elements_produce_different_fingerprints() -> None:
    elements_a = (CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "a"}),)
    elements_b = (CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "b"}),)

    assert compute_fingerprint(_snapshot(elements_a)) != compute_fingerprint(_snapshot(elements_b))


def test_elements_without_id_or_data_testid_are_ignored() -> None:
    with_noise = (
        CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "a"}),
        CollectedElement(tag_name="div", text="decorative", visible=True, attributes={}),
    )
    without_noise = (CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "a"}),)

    assert compute_fingerprint(_snapshot(with_noise)) == compute_fingerprint(_snapshot(without_noise))


def test_empty_snapshot_is_stable() -> None:
    assert compute_fingerprint(_snapshot(())) == compute_fingerprint(_snapshot(()))
