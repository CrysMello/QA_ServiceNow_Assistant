"""Reporting Engine (SAD Cap. 22).

Consolidates execution results, generates reports in a configurable
format and produces aggregate metrics (SAD 22.1). Reporting Engine "nao
implementa regras de negocio" (SAD 22.8) - it only renders and persists
whatever ExecutionResult a caller (future Workflow Engine) hands it.

Its own in-memory history of recorded ExecutionResults plays the role of
SAD 22.3's "Execution Collector" (the real one depends on Workflow
Engine, which does not exist yet - the same deliberate scope boundary
used throughout this codebase for not-yet-implemented upstream modules).
ExecutionMetricsCalculator plays "Metrics Calculator"; JsonReportFormatter/
HtmlReportFormatter play "Report Generator" (no separate "Template
Engine" module exists in the official prompt sequence, so formatting is
implemented directly as pure domain services); ReportRepositoryPort plays
"State... (Report) Repository"; LogPort satisfies "Audit Registry" (SAD
22.3 depends on Log Engine), matching every other module's approach.

Only "json" and "html" are supported formats: SAD 22.5 illustrates JSON,
HTML, PDF, CSV and Console, but ReportingConfiguration/ConfigurationValidator
(Configuration Manager, Prompt 2) already narrowed this to {"html", "json"}
per SRS Cap.7 - this module respects that existing, already-validated
constraint rather than re-opening it.
"""

from __future__ import annotations

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.report_repository_port import (
    ReportRepositoryPort,
)
from qa_servicenow_assistant.domain.exceptions.reporting import (
    ReportPersistenceError,
    UnsupportedReportFormatError,
)
from qa_servicenow_assistant.domain.services.execution_metrics_calculator import (
    ExecutionMetricsCalculator,
)
from qa_servicenow_assistant.domain.services.html_report_formatter import (
    HtmlReportFormatter,
)
from qa_servicenow_assistant.domain.services.json_report_formatter import (
    JsonReportFormatter,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ReportingConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.execution_metrics import (
    ExecutionMetrics,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.report_generation_result import (
    ReportGenerationResult,
)

_FORMATTERS = {
    "json": JsonReportFormatter(),
    "html": HtmlReportFormatter(),
}


class ReportingEngine:
    def __init__(
        self,
        repository: ReportRepositoryPort,
        log_port: LogPort,
        configuration: ReportingConfiguration | None = None,
        metrics_calculator: ExecutionMetricsCalculator | None = None,
    ) -> None:
        self._repository = repository
        self._log_port = log_port
        self._configuration = configuration or ReportingConfiguration()
        self._metrics_calculator = metrics_calculator or ExecutionMetricsCalculator()
        self._results: list[ExecutionResult] = []

    @property
    def history(self) -> tuple[ExecutionResult, ...]:
        """All ExecutionResults recorded so far, oldest first (SAD 22.3 -
        Execution Collector)."""
        return tuple(self._results)

    def generate_report(
        self, result: ExecutionResult, *, format: str | None = None
    ) -> ReportGenerationResult:
        """Record result (for metrics) and render+persist a report for it
        (SAD 22.2 - "Consolidar os resultados"; "Gerar relatorios em
        diferentes formatos"). format defaults to
        self._configuration.format (already validated by
        ConfigurationValidator); an explicit override outside the
        supported set raises UnsupportedReportFormatError - a
        caller-contract violation, not an operational failure.

        Never raises for expected failures (persistence I/O errors);
        those are logged (SAD 22.8 - rastreabilidade) and returned as a
        failed ReportGenerationResult.
        """
        selected_format = format or self._configuration.format
        formatter = _FORMATTERS.get(selected_format)
        if formatter is None:
            raise UnsupportedReportFormatError(
                f"Unsupported report format: {selected_format!r} "
                f"(supported: {sorted(_FORMATTERS)})"
            )

        self._results.append(result)

        content = formatter.format(result)
        file_name = f"{result.execution_id}.{formatter.file_extension}"

        try:
            report_path = self._repository.save(content, file_name)
        except ReportPersistenceError as error:
            self._log_port.error(
                "Report generation failed",
                execution_id=result.execution_id,
                workflow_id=result.workflow_id,
                error=str(error),
            )
            return ReportGenerationResult(success=False, report_path=None, error_message=str(error))

        self._log_port.info(
            "Report generated",
            execution_id=result.execution_id,
            workflow_id=result.workflow_id,
            status=result.status.value,
            report_path=str(report_path),
        )
        return ReportGenerationResult(success=True, report_path=report_path)

    def calculate_metrics(self) -> ExecutionMetrics:
        """Aggregate indicators over every ExecutionResult recorded so far
        (SAD 22.7 - Metricas Produzidas)."""
        return self._metrics_calculator.calculate(self._results)
