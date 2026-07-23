"""HtmlReportFormatter: renders an ExecutionResult as a self-contained
HTML report string (SAD 22.5 - formato "HTML: Visualizacao em navegador").

Pure domain logic (SAD 8.7); ReportRepositoryPort implementations persist
the string this produces. Every value that may originate from external
data (ServiceNow field values surfaced in errors/log_summary/evidence
descriptions) is HTML-escaped before being embedded, since this output is
meant to be opened directly in a browser.
"""

from __future__ import annotations

from html import escape

from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Execution Report - {execution_id}</title>
</head>
<body>
<h1>Execution Report</h1>
<table>
<tr><th>Execution ID</th><td>{execution_id}</td></tr>
<tr><th>Workflow</th><td>{workflow_id}</td></tr>
<tr><th>Status</th><td>{status}</td></tr>
<tr><th>Duration (ms)</th><td>{duration_ms}</td></tr>
<tr><th>Retry attempts</th><td>{retry_attempts}</td></tr>
<tr><th>Checkpoints used</th><td>{checkpoints_used}</td></tr>
<tr><th>Completed at</th><td>{completed_at}</td></tr>
</table>
<h2>Evidence</h2>
<ul>{evidence_items}</ul>
<h2>Log Summary</h2>
<ul>{log_items}</ul>
<h2>Errors</h2>
<ul>{error_items}</ul>
</body>
</html>
"""


class HtmlReportFormatter:
    file_extension = "html"

    def format(self, result: ExecutionResult) -> str:
        evidence_items = "".join(
            f"<li>{escape(item.description)}: {escape(item.path)}</li>" for item in result.evidence
        )
        log_items = "".join(f"<li>{escape(entry)}</li>" for entry in result.log_summary)
        error_items = "".join(f"<li>{escape(entry)}</li>" for entry in result.errors)

        return _TEMPLATE.format(
            execution_id=escape(result.execution_id),
            workflow_id=escape(result.workflow_id),
            status=escape(result.status.value),
            duration_ms=result.duration_ms,
            retry_attempts=result.retry_attempts,
            checkpoints_used=result.checkpoints_used,
            completed_at=escape(result.completed_at.isoformat()),
            evidence_items=evidence_items or "<li>(none)</li>",
            log_items=log_items or "<li>(none)</li>",
            error_items=error_items or "<li>(none)</li>",
        )
