"""Application Controller (Module Specifications Cap. 20 - "Coordenacao
da aplicacao"; ADR-0015 - no dedicated SAD chapter exists).

Composition root: the only module in this codebase authorized to
construct concrete infrastructure adapters directly
(JsonConfigurationRepository, LoguruLogAdapter, JsonKnowledgeRepository,
JsonFileCheckpointRepository, FileReportRepository, ZipExportRepository,
PlaywrightBrowserManager). Every other module stays decoupled via Ports
by design - this is where that decoupling terminates.

Bootstraps, in order (SAD 3.4 - Fluxo Arquitetural de Alto Nivel):
1. Load configuration (LoadConfigurationUseCase, Prompt 2).
2. Initialize logging in two phases - a provisional LoguruLogAdapter with
   the default LoggingConfiguration() so step 1 itself can log, then a
   real one rebuilt from the loaded LoggingConfiguration (SAD 21.7:
   "Application Controller: Inicializar configuracoes"; SAD 24.3: Log
   Engine's "Log Manager" depends on Application Controller for
   orchestration).
3. Load the Knowledge Base (JsonKnowledgeRepository + KnowledgeManager,
   Prompt 18). Raises on incompatible version/missing manifest - fails
   fast during initialization (SAD 11.8), not caught here.
4. Compose the session-level cross-cutting services: Retry Engine,
   Checkpoint Engine, Reporting Engine, Export Engine, and Workflow
   Engine (built from the first three).
5. Construct (but do not start) the browser manager - start()/stop() or
   the context manager protocol control its lifecycle explicitly (SAD
   10.7 - "recursos devem ser liberados corretamente ao final da
   execucao").

Deliberate scope boundaries (ADR-0015), documented rather than silently
absent:
- Does not read/interpret the Excel spreadsheet: Excel Importer has no
  SAD chapter or Module Specifications Prompt of its own.
- Does not parse CLI arguments: CLI is a later prompt (22); this class
  receives an already-built LoadConfigurationRequest.
- Does not pre-compose Navigation Engine, Page Recognition, Automation
  Engine, Frame Resolution Engine or Selector Resolution Engine - those
  are STEP-level concerns (used inside a WorkflowStep.action), the same
  principle WorkflowStep itself already applies to its caller-supplied
  callables. Whoever assembles a concrete Workflow instantiates those
  using new_page()/knowledge as building blocks.
- Does not assemble any concrete Workflow (e.g. "create an incident") -
  that needs data from the nonexistent Excel Importer and ServiceNow
  business rules, which no module in this codebase implements.
"""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.application.services.export.export_engine import (
    ExportEngine,
)
from qa_servicenow_assistant.application.services.knowledge.knowledge_manager import (
    KnowledgeManager,
)
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.application.services.retry.retry_engine import RetryEngine
from qa_servicenow_assistant.application.services.workflow.workflow_engine import (
    WorkflowEngine,
)
from qa_servicenow_assistant.application.use_cases.load_configuration import (
    LoadConfigurationRequest,
    LoadConfigurationUseCase,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ApplicationConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.execution_context import (
    ExecutionContext,
)
from qa_servicenow_assistant.domain.value_objects.execution_metrics import (
    ExecutionMetrics,
)
from qa_servicenow_assistant.domain.value_objects.export_request import ExportRequest
from qa_servicenow_assistant.domain.value_objects.export_result import ExportResult
from qa_servicenow_assistant.domain.value_objects.workflow import Workflow
from qa_servicenow_assistant.domain.value_objects.workflow_result import WorkflowResult
from qa_servicenow_assistant.infrastructure.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from qa_servicenow_assistant.infrastructure.checkpoints.json_file_checkpoint_repository import (
    JsonFileCheckpointRepository,
)
from qa_servicenow_assistant.infrastructure.config.json_configuration_repository import (
    JsonConfigurationRepository,
)
from qa_servicenow_assistant.infrastructure.export.zip_export_repository import (
    ZipExportRepository,
)
from qa_servicenow_assistant.infrastructure.logging.loguru_log_adapter import (
    LoguruLogAdapter,
)
from qa_servicenow_assistant.infrastructure.persistence.json_knowledge_repository import (
    JsonKnowledgeRepository,
)
from qa_servicenow_assistant.infrastructure.reporting.file_report_repository import (
    FileReportRepository,
)


class ApplicationController:
    """Bootstraps the application and exposes the minimal facade a
    caller (a future CLI, or a test) needs to assemble and run
    workflows: new_page(), run_workflow(), calculate_metrics(),
    export(), and read-only access to the composed session-level
    services."""

    def __init__(
        self,
        request: LoadConfigurationRequest,
        *,
        expected_knowledge_base_version: str = "1.0",
    ) -> None:
        bootstrap_log_port = LoguruLogAdapter()
        configuration = LoadConfigurationUseCase(
            JsonConfigurationRepository(), bootstrap_log_port
        ).execute(request)
        self._configuration = configuration

        self._log_port: LogPort = LoguruLogAdapter(configuration.logging)

        self._knowledge = KnowledgeManager(
            JsonKnowledgeRepository(
                configuration.knowledge_base_path,
                self._log_port,
                expected_knowledge_base_version,
            ),
            self._log_port,
        )

        self._retry_engine = RetryEngine(self._log_port, configuration.retry)
        self._checkpoint_engine = CheckpointEngine(
            JsonFileCheckpointRepository(configuration.checkpoints), self._log_port
        )
        self._reporting_engine = ReportingEngine(
            FileReportRepository(configuration.reporting), self._log_port, configuration.reporting
        )
        self._export_engine = ExportEngine(
            ZipExportRepository(configuration.export), self._log_port
        )
        self._workflow_engine = WorkflowEngine(
            self._log_port,
            retry_engine=self._retry_engine,
            checkpoint_engine=self._checkpoint_engine,
            reporting_engine=self._reporting_engine,
        )

        self._browser_manager = PlaywrightBrowserManager(configuration.browser, self._log_port)

        self._log_port.info(
            "Application Controller initialized",
            instance_url=configuration.instance_url,
            knowledge_base_path=str(configuration.knowledge_base_path),
        )

    @property
    def configuration(self) -> ApplicationConfiguration:
        return self._configuration

    @property
    def log_port(self) -> LogPort:
        return self._log_port

    @property
    def knowledge(self) -> KnowledgeManager:
        return self._knowledge

    @property
    def retry_engine(self) -> RetryEngine:
        return self._retry_engine

    @property
    def checkpoint_engine(self) -> CheckpointEngine:
        return self._checkpoint_engine

    @property
    def reporting_engine(self) -> ReportingEngine:
        return self._reporting_engine

    @property
    def export_engine(self) -> ExportEngine:
        return self._export_engine

    @property
    def workflow_engine(self) -> WorkflowEngine:
        return self._workflow_engine

    def start(self) -> None:
        """Launch the browser (SAD 10.7 - lifecycle explicitly controlled,
        never launched implicitly as a constructor side effect)."""
        self._browser_manager.start()

    def stop(self) -> None:
        self._browser_manager.stop()

    def new_page(self) -> Any:
        return self._browser_manager.new_page()

    def run_workflow(
        self, workflow: Workflow, context: ExecutionContext, *, resume: bool = False
    ) -> WorkflowResult:
        return self._workflow_engine.execute(workflow, context, resume=resume)

    def calculate_metrics(self) -> ExecutionMetrics:
        return self._reporting_engine.calculate_metrics()

    def export(self, request: ExportRequest) -> ExportResult:
        return self._export_engine.export(request)

    def __enter__(self) -> "ApplicationController":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.stop()
