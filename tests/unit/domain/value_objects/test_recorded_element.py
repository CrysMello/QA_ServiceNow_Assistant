"""Unit tests for RecordedElement."""

from __future__ import annotations

from datetime import datetime, timezone

from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)
from qa_servicenow_assistant.domain.value_objects.recorded_element import (
    RecordedElement,
)


def test_recorded_at_is_set_automatically() -> None:
    element = CollectedElement(tag_name="button", text="Submit", visible=True)
    before = datetime.now(timezone.utc)

    record = RecordedElement(element=element, label="primary_action", page_url="https://dev.service-now.com/home")

    after = datetime.now(timezone.utc)
    assert before <= record.recorded_at <= after


def test_holds_element_label_and_page_url() -> None:
    element = CollectedElement(
        tag_name="input", text="", visible=True, attributes={"name": "username"}
    )

    record = RecordedElement(element=element, label="login_field", page_url="https://dev.service-now.com/login")

    assert record.element == element
    assert record.label == "login_field"
    assert record.page_url == "https://dev.service-now.com/login"
