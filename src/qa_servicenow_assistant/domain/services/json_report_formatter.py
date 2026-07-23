"""JsonReportFormatter: renders an ExecutionResult as a JSON report
string (SAD 22.5 - formato "JSON: Integracao com outras aplicacoes").

Pure domain logic (SAD 8.7); ReportRepositoryPort implementations persist
the string this produces.
"""

from __future__ import annotations

import json

from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)

class JsonReportFormatter:
    file_extension = "json"

    def format(self, result: ExecutionResult) -> str:
        payload = {
            "execution_id": result.execution_id,
            "workflow_id": result.workflow_id,
            "status": result.status.value,
            "duration_ms": result.duration_ms,
            "evidence": [
                {"description": item.description, "path": item.path} for item in result.evidence
            ],
            "log_summary": list(result.log_summary),
            "errors": list(result.errors),
            "retry_attempts": result.retry_attempts,
            "checkpoints_used": result.checkpoints_used,
            "completed_at": result.completed_at.isoformat(),
        }
        return json.dumps(payload, indent=2)
