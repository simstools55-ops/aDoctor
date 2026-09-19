from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ClinicalPipelineResult:
    pipeline_run_id: str
    case_id: str
    medical_record_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    completed_steps: tuple[str, ...]
    failed_step: str | None
    final_diagnosis_id: str | None
    referral_id: str | None
    case_status: str
    errors: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_run_id": self.pipeline_run_id,
            "case_id": self.case_id,
            "medical_record_id": self.medical_record_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "completed_steps": list(self.completed_steps),
            "failed_step": self.failed_step,
            "final_diagnosis_id": self.final_diagnosis_id,
            "referral_id": self.referral_id,
            "case_status": self.case_status,
            "errors": list(self.errors),
        }
