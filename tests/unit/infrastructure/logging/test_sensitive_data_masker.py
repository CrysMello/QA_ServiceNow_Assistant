"""Unit tests for mask_sensitive_data (RNF-001, AI Coding Standards Sec.17)."""

from __future__ import annotations

from qa_servicenow_assistant.infrastructure.logging.sensitive_data_masker import (
    MASK_PLACEHOLDER,
    mask_sensitive_data,
)


def test_masks_top_level_sensitive_key() -> None:
    result = mask_sensitive_data({"password": "hunter2", "username": "operator"})

    assert result["password"] == MASK_PLACEHOLDER
    assert result["username"] == "operator"


def test_masks_nested_dict_values() -> None:
    result = mask_sensitive_data({"request": {"headers": {"Authorization": "Bearer xyz"}}})

    assert result["request"]["headers"]["Authorization"] == MASK_PLACEHOLDER


def test_masks_list_of_dicts() -> None:
    result = mask_sensitive_data([{"token": "abc"}, {"note": "ok"}])

    assert result[0]["token"] == MASK_PLACEHOLDER
    assert result[1]["note"] == "ok"


def test_case_insensitive_key_matching() -> None:
    result = mask_sensitive_data({"COOKIE": "abc", "Api_Key": "def"})

    assert result["COOKIE"] == MASK_PLACEHOLDER
    assert result["Api_Key"] == MASK_PLACEHOLDER


def test_substring_key_matching() -> None:
    result = mask_sensitive_data({"auth_token": "abc", "refresh_token": "def"})

    assert result["auth_token"] == MASK_PLACEHOLDER
    assert result["refresh_token"] == MASK_PLACEHOLDER


def test_non_sensitive_data_is_unchanged() -> None:
    payload = {"instance_url": "https://dev.service-now.com", "retry_max_attempts": 3}

    assert mask_sensitive_data(payload) == payload


def test_non_dict_values_pass_through() -> None:
    assert mask_sensitive_data("plain string") == "plain string"
    assert mask_sensitive_data(42) == 42
    assert mask_sensitive_data(None) is None
