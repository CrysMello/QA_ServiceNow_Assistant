"""Unit tests for BrowserSnapshot / CollectedElement."""

from __future__ import annotations

from datetime import datetime, timezone

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)


def test_browser_snapshot_defaults() -> None:
    before = datetime.now(timezone.utc)

    snapshot = BrowserSnapshot(url="https://dev.service-now.com", title="Home", html="<html></html>")

    after = datetime.now(timezone.utc)
    assert snapshot.elements == ()
    assert before <= snapshot.collected_at <= after


def test_collected_element_defaults_to_empty_attributes() -> None:
    element = CollectedElement(tag_name="button", text="Submit", visible=True)

    assert element.attributes == {}


def test_browser_snapshot_holds_collected_elements() -> None:
    element = CollectedElement(
        tag_name="input",
        text="",
        visible=True,
        attributes={"name": "username"},
    )

    snapshot = BrowserSnapshot(
        url="https://dev.service-now.com",
        title="Login",
        html="<html></html>",
        elements=(element,),
    )

    assert snapshot.elements == (element,)
