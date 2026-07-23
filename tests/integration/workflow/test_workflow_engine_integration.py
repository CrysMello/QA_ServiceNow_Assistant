"""Integration test for WorkflowEngine wiring together REAL Navigation
Engine (with a real Chromium browser via PlaywrightBrowserManager), REAL
Retry Engine, REAL Checkpoint Engine (backed by JsonFileCheckpointRepository
over tmp_path) and REAL Reporting Engine (backed by FileReportRepository
over tmp_path) - demonstrating the wiring these modules' own docstrings
have, until now, deliberately deferred to "a future Workflow Engine"
(SAD Cap. 12; SAD 12.6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.application.services.retry.retry_engine import RetryEngine
from qa_servicenow_assistant.application.services.workflow.workflow_engine import (
    WorkflowEngine,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
    CheckpointConfiguration,
    ReportingConfiguration,
    RetryConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_state import WorkflowState
from qa_servicenow_assistant.domain.value_objects.workflow_step import WorkflowStep
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.browser.playwright_navigation_executor import (
    PlaywrightNavigationExecutor,
)
from qa_servicenow_assistant.infrastructure.checkpoints.json_file_checkpoint_repository import (
    JsonFileCheckpointRepository,
)
from qa_servicenow_assistant.infrastructure.reporting.file_report_repository import (
    FileReportRepository,
)

_TARGET_PAGE_URL = "data:text/html,<html><head><title>Target Page</title></head><body></body></html>"


class RecordingLogPort(LogPort):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def bind(self, **context: Any) -> "RecordingLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def warning(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


class TitleMatchesValidator(NavigationValidationPort):
    def __init__(self, expected_title: str) -> None:
        self._expected_title = expected_title

    def validate(self, page: Any, target: PageIdentifier) -> bool:
        return page.title() == self._expected_title


def test_workflow_engine_wires_real_navigation_retry_checkpoint_and_reporting(
    tmp_path: Path,
) -> None:
    log_port = RecordingLogPort()

    browser_manager = PlaywrightBrowserManager(BrowserConfiguration(), log_port)
    navigation_engine = NavigationEngine(
        PlaywrightNavigationExecutor(), TitleMatchesValidator("Target Page"), log_port
    )
    retry_engine = RetryEngine(
        log_port, configuration=RetryConfiguration(max_attempts=2, backoff_strategy="none")
    )
    checkpoint_engine = CheckpointEngine(
        JsonFileCheckpointRepository(CheckpointConfiguration(directory=tmp_path / "checkpoints")),
        log_port,
    )
    reporting_configuration = ReportingConfiguration(format="json", directory=tmp_path / "reports")
    reporting_engine = ReportingEngine(
        FileReportRepository(reporting_configuration), log_port, reporting_configuration
    )

    def navigate_step(context: ExecutionContext) -> None:
        page = context.data["page"]
        result = navigation_engine.navigate(page, PageIdentifier(key="target"), _TARGET_PAGE_URL)
        if not result.success:
            raise RuntimeError(result.error_message)

    def verify_step(context: ExecutionContext) -> None:
        page = context.data["page"]
        if page.title() != "Target Page":
            raise RuntimeError("Title mismatch after navigation")

    workflow = Workflow(
        key="open_target_page",
        description="Navigate to the target page and verify it loaded",
        steps=(
            WorkflowStep(key="navigate", description="Navigate to target", action=navigate_step),
            WorkflowStep(key="verify", description="Verify page title", action=verify_step),
        ),
    )

    workflow_engine = WorkflowEngine(
        log_port,
        retry_engine=retry_engine,
        checkpoint_engine=checkpoint_engine,
        reporting_engine=reporting_engine,
    )

    browser_manager.start()
    try:
        page = browser_manager.new_page()
        context = ExecutionContext(execution_id="exec-real-1", workflow_id="open_target_page")
        context.data["page"] = page
        result = workflow_engine.execute(workflow, context)
    finally:
        browser_manager.stop()

    assert result.final_state == WorkflowState.COMPLETED
    assert "Workflow completed" in log_port.messages

    checkpoint_history = checkpoint_engine.history("exec-real-1")
    assert [c.last_completed_step for c in checkpoint_history] == ["navigate", "verify"]

    report_path = tmp_path / "reports" / "exec-real-1.json"
    assert report_path.exists()
    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_data["status"] == "success"


def test_workflow_engine_resumes_a_real_execution_after_a_simulated_restart(tmp_path: Path) -> None:
    log_port = RecordingLogPort()
    checkpoint_configuration = CheckpointConfiguration(directory=tmp_path / "checkpoints")

    # Simulate a prior process having already completed the first step.
    first_run_repository = JsonFileCheckpointRepository(checkpoint_configuration)
    first_run_repository.save(
        Checkpoint(execution_id="exec-real-2", workflow_id="wf", last_completed_step="step_one")
    )

    visited: list[str] = []
    workflow = Workflow(
        key="wf",
        description="wf",
        steps=(
            WorkflowStep(key="step_one", description="one", action=lambda ctx: visited.append("step_one")),
            WorkflowStep(key="step_two", description="two", action=lambda ctx: visited.append("step_two")),
        ),
    )

    checkpoint_engine = CheckpointEngine(
        JsonFileCheckpointRepository(checkpoint_configuration), log_port
    )
    workflow_engine = WorkflowEngine(log_port, checkpoint_engine=checkpoint_engine)
    context = ExecutionContext(execution_id="exec-real-2", workflow_id="wf")

    result = workflow_engine.execute(workflow, context, resume=True)

    assert result.final_state == WorkflowState.COMPLETED
    assert visited == ["step_two"]  # step_one's action never re-ran
