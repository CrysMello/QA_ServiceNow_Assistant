"""Unit tests for CheckpointSerializer (SAD 20.3 - State Serializer)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from qa_servicenow_assistant.domain.services.checkpoint_serializer import (
    CheckpointSerializer,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


def test_round_trip_preserves_all_fields() -> None:
    serializer = CheckpointSerializer()
    checkpoint = Checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="navigate_to_incident_form",
        page=PageIdentifier(key="incident_form"),
        temporary_data={"incident_number": "INC0010001", "retry_count": 2},
        partial_result="in_progress",
        created_at=datetime(2026, 7, 22, 12, 30, 0, tzinfo=timezone.utc),
    )

    data = serializer.to_dict(checkpoint)
    restored = serializer.from_dict(data)

    assert restored == checkpoint


def test_round_trip_with_no_page() -> None:
    serializer = CheckpointSerializer()
    checkpoint = Checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="start",
    )

    restored = serializer.from_dict(serializer.to_dict(checkpoint))

    assert restored.page is None
    assert restored.temporary_data == {}
    assert restored.partial_result == ""


def test_to_dict_produces_json_safe_primitives() -> None:
    serializer = CheckpointSerializer()
    checkpoint = Checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="start",
        page=PageIdentifier(key="home"),
    )

    data = serializer.to_dict(checkpoint)

    assert data["page_key"] == "home"
    assert isinstance(data["created_at"], str)


def test_from_dict_raises_on_missing_required_field() -> None:
    serializer = CheckpointSerializer()

    with pytest.raises(KeyError):
        serializer.from_dict({"workflow_id": "w", "last_completed_step": "s", "created_at": "x"})


def test_from_dict_raises_on_malformed_timestamp() -> None:
    serializer = CheckpointSerializer()

    with pytest.raises(ValueError):
        serializer.from_dict(
            {
                "execution_id": "exec-1",
                "workflow_id": "w",
                "last_completed_step": "s",
                "created_at": "not-a-timestamp",
            }
        )
