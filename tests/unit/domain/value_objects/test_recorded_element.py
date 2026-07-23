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

    record = RecordedElement(
        element=element,
        execution_id="exec-1",
        label="primary_action",
        page_url="https://dev.service-now.com/home",
    )

    after = datetime.now(timezone.utc)
    assert before <= record.recorded_at <= after


def test_holds_execution_id_label_and_page_url() -> None:
    element = CollectedElement(
        tag_name="input", text="", visible=True, attributes={"name": "username"}
    )

    record = RecordedElement(
        element=element,
        execution_id="exec-1",
        label="login_field",
        page_url="https://dev.service-now.com/login",
    )

    assert record.element == element
    assert record.execution_id == "exec-1"
    assert record.label == "login_field"
    assert record.page_url == "https://dev.service-now.com/login"


def test_page_id_defaults_to_none() -> None:
    element = CollectedElement(tag_name="button", text="Submit", visible=True)

    record = RecordedElement(
        element=element,
        execution_id="exec-1",
        label="primary_action",
        page_url="https://dev.service-now.com/home",
    )

    assert record.page_id is None


def test_page_id_can_be_supplied() -> None:
    element = CollectedElement(tag_name="button", text="Submit", visible=True)

    record = RecordedElement(
        element=element,
        execution_id="exec-1",
        label="primary_action",
        page_url="https://dev.service-now.com/home",
        page_id="home",
    )

    assert record.page_id == "home"


def test_element_id_prefers_id_over_data_testid() -> None:
    element = CollectedElement(
        tag_name="button",
        text="Submit",
        visible=True,
        attributes={"id": "submit-btn", "data_testid": "submit"},
    )

    record = RecordedElement(
        element=element, execution_id="exec-1", label="primary_action", page_url="https://x"
    )

    assert record.element_id == "submit-btn"


def test_element_id_falls_back_to_data_testid() -> None:
    element = CollectedElement(
        tag_name="button", text="Submit", visible=True, attributes={"data_testid": "submit"}
    )

    record = RecordedElement(
        element=element, execution_id="exec-1", label="primary_action", page_url="https://x"
    )

    assert record.element_id == "submit"


def test_element_id_is_none_when_neither_attribute_is_present() -> None:
    element = CollectedElement(tag_name="div", text="decorative", visible=True)

    record = RecordedElement(
        element=element, execution_id="exec-1", label="primary_action", page_url="https://x"
    )

    assert record.element_id is None
