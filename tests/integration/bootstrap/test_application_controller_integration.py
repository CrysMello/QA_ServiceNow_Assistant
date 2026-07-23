"""Integration tests for ApplicationController (ADR-0015).

Uses real files (config, Knowledge Base, checkpoints, reports) under
tmp_path and a real Chromium browser - ApplicationController is a
composition root that only ever constructs real infrastructure adapters,
so faking them would not exercise what this class actually does.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_servicenow_assistant.bootstrap.application_controller import (
    ApplicationController,
)
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.application.use_cases.load_configuration import (
    LoadConfigurationRequest,
)
from qa_servicenow_assistant.domain.exceptions.knowledge_base import (
    IncompatibleKnowledgeBaseVersionError,
    KnowledgeBaseNotFoundError,
)
from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.domain.value_objects.export_request import ExportRequest
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)

_TARGET_PAGE_URL = "data:text/html,<html><head><title>Target Page</title></head><body></body></html>"


class _AlwaysValidValidator(NavigationValidationPort):
    def validate(self, page, target) -> bool:
        return True


def _write_knowledge_base(directory: Path, *, version: str = "1.0") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    (directory / "pages.json").write_text(
        json.dumps([{"key": "target_page", "url_pattern": "/target"}]), encoding="utf-8"
    )


def make_request(tmp_path: Path, *, kb_version: str = "1.0", with_kb: bool = True) -> LoadConfigurationRequest:
    spreadsheet = tmp_path / "input.xlsx"
    spreadsheet.write_bytes(b"fake-xlsx-content")

    knowledge_base_dir = tmp_path / "knowledge_base"
    if with_kb:
        _write_knowledge_base(knowledge_base_dir, version=kb_version)
    else:
        knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    # Redirect checkpoints/reporting/export output under tmp_path via a
    # real config file, instead of the default relative directories
    # (temp/checkpoints, reports, exports) - keeps this test from writing
    # outside tmp_path regardless of the process' working directory.
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "checkpoints": {"directory": str(tmp_path / "checkpoints")},
                "reporting": {"directory": str(tmp_path / "reports")},
                "export": {"directory": str(tmp_path / "exports")},
            }
        ),
        encoding="utf-8",
    )

    return LoadConfigurationRequest(
        spreadsheet_path=spreadsheet,
        knowledge_base_path=knowledge_base_dir,
        instance_url="https://dev12345.service-now.com",
        config_file_path=config_file,
    )


def test_initializes_successfully_with_valid_configuration_and_knowledge_base(tmp_path: Path) -> None:
    request = make_request(tmp_path)

    controller = ApplicationController(request)

    assert controller.configuration.instance_url == "https://dev12345.service-now.com"
    assert controller.knowledge.get_page("target_page") is not None
    assert controller.retry_engine is not None
    assert controller.checkpoint_engine is not None
    assert controller.reporting_engine is not None
    assert controller.export_engine is not None
    assert controller.workflow_engine is not None


def test_raises_when_knowledge_base_manifest_is_missing(tmp_path: Path) -> None:
    request = make_request(tmp_path, with_kb=False)

    with pytest.raises(KnowledgeBaseNotFoundError):
        ApplicationController(request)


def test_raises_when_knowledge_base_version_is_incompatible(tmp_path: Path) -> None:
    request = make_request(tmp_path, kb_version="9.9")

    with pytest.raises(IncompatibleKnowledgeBaseVersionError):
        ApplicationController(request)


def test_expected_knowledge_base_version_is_configurable(tmp_path: Path) -> None:
    request = make_request(tmp_path, kb_version="2.0")

    controller = ApplicationController(request, expected_knowledge_base_version="2.0")

    assert controller.knowledge.validate_version() is True


def test_browser_lifecycle_via_explicit_start_stop(tmp_path: Path) -> None:
    controller = ApplicationController(make_request(tmp_path))

    controller.start()
    try:
        page = controller.new_page()
        assert page is not None
    finally:
        controller.stop()


def test_browser_lifecycle_via_context_manager(tmp_path: Path) -> None:
    controller = ApplicationController(make_request(tmp_path))

    with controller as app:
        page = app.new_page()
        assert page is not None


def test_run_workflow_end_to_end_saves_checkpoints_and_report(tmp_path: Path) -> None:
    controller = ApplicationController(make_request(tmp_path))
    navigation_engine = NavigationEngine(
        PlaywrightNavigationExecutor(), _AlwaysValidValidator(), controller.log_port
    )

    def navigate_step(context: ExecutionContext) -> None:
        page = context.data["page"]
        result = navigation_engine.navigate(page, PageIdentifier(key="target_page"), _TARGET_PAGE_URL)
        if not result.success:
            raise RuntimeError(result.error_message)

    workflow = Workflow(
        key="open_target_page",
        description="Navigate to the target page",
        steps=(WorkflowStep(key="navigate", description="Navigate", action=navigate_step),),
    )

    with controller as app:
        page = app.new_page()
        context = ExecutionContext(execution_id="exec-real-1", workflow_id="open_target_page")
        context.data["page"] = page
        result = app.run_workflow(workflow, context)

    assert result.final_state == WorkflowState.COMPLETED

    checkpoint_history = controller.checkpoint_engine.history("exec-real-1")
    assert [c.last_completed_step for c in checkpoint_history] == ["navigate"]

    metrics = controller.calculate_metrics()
    assert metrics.total_executions == 1
    assert metrics.success_count == 1

    report_path = Path(controller.configuration.reporting.directory) / "exec-real-1.html"
    assert report_path.exists()


def test_export_uses_the_composed_export_engine(tmp_path: Path) -> None:
    controller = ApplicationController(make_request(tmp_path))
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("evidence", encoding="utf-8")

    result = controller.export(
        ExportRequest(
            execution_id="exec-real-2",
            items=(ExportItem(description="evidence", source_path=artifact),),
        )
    )

    assert result.success is True
    assert result.archive_path.exists()
