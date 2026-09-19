from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any, Callable

from src.doctor.events import MedicalRecordEventLog
from .models import ClinicalPipelineResult


class ClinicalPipelineError(RuntimeError):
    pass


def _run_id(now: datetime) -> str:
    return f"RUN-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class ClinicalPipelineOrchestrator:
    def __init__(
        self,
        *,
        event_log: MedicalRecordEventLog,
        evidence_engine: Any,
        vital_signs_engine: Any,
        findings_engine: Any,
        differential_engine: Any,
        final_diagnosis_engine: Any,
        treatment_engine: Any,
        referral_engine: Any,
        policy: dict[str, Any],
    ) -> None:
        self.event_log = event_log
        self.evidence_engine = evidence_engine
        self.vital_signs_engine = vital_signs_engine
        self.findings_engine = findings_engine
        self.differential_engine = differential_engine
        self.final_diagnosis_engine = final_diagnosis_engine
        self.treatment_engine = treatment_engine
        self.referral_engine = referral_engine
        self.policy = policy

    def run(
        self,
        medical_record: dict[str, Any],
        *,
        run_key: str,
        observation_callbacks: dict[str, Callable[[], dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        existing = self._find_existing(medical_record, run_key)
        if existing is not None:
            return existing

        started = datetime.now(timezone.utc)
        run_id = _run_id(started)
        completed_steps: list[str] = []
        errors: list[dict[str, Any]] = []
        failed_step: str | None = None

        callbacks = observation_callbacks or {}
        observation_successes = 0

        for step in (
            "SEARCH_CONSOLE_OBSERVATION",
            "SERP_OBSERVATION",
            "ARTICLE_SNAPSHOT_OBSERVATION",
        ):
            callback = callbacks.get(step)
            if callback is None:
                errors.append({
                    "step": step,
                    "code": "OBSERVATION_CALLBACK_MISSING",
                    "message": f"No callback supplied for {step}",
                    "recoverable": True,
                })
                continue
            try:
                callback()
                completed_steps.append(step)
                observation_successes += 1
            except Exception as exc:
                errors.append({
                    "step": step,
                    "code": exc.__class__.__name__,
                    "message": str(exc),
                    "recoverable": True,
                })

        if observation_successes == 0:
            failed_step = "OBSERVATION"
            medical_record["case_status"] = "ERROR"
            return self._finish(
                medical_record=medical_record,
                run_id=run_id,
                run_key=run_key,
                started=started,
                completed_steps=completed_steps,
                failed_step=failed_step,
                errors=errors,
            )

        clinical_steps = [
            ("EVIDENCE_EXTRACTION", lambda: self.evidence_engine.extract_all(medical_record)),
            (
                "VITAL_SIGNS",
                lambda: self.vital_signs_engine.calculate(
                    medical_record, idempotency_key=f"{run_key}:vitals"
                ),
            ),
            ("FINDINGS", lambda: self.findings_engine.generate_all(medical_record)),
            (
                "DIFFERENTIAL_DIAGNOSIS",
                lambda: self.differential_engine.assess(
                    medical_record, idempotency_key=f"{run_key}:differential"
                ),
            ),
            (
                "FINAL_DIAGNOSIS",
                lambda: self.final_diagnosis_engine.confirm(
                    medical_record, idempotency_key=f"{run_key}:diagnosis"
                ),
            ),
            (
                "TREATMENT_RECOMMENDATION",
                lambda: self.treatment_engine.recommend(
                    medical_record, idempotency_key=f"{run_key}:treatment"
                ),
            ),
            (
                "REFERRAL",
                lambda: self.referral_engine.issue(
                    medical_record, idempotency_key=f"{run_key}:referral"
                ),
            ),
        ]

        for step, action in clinical_steps:
            try:
                action()
                completed_steps.append(step)
            except Exception as exc:
                errors.append({
                    "step": step,
                    "code": exc.__class__.__name__,
                    "message": str(exc),
                    "recoverable": step == "REFERRAL",
                })
                failed_step = step
                if step == "REFERRAL":
                    break
                medical_record["case_status"] = "ERROR"
                break

        return self._finish(
            medical_record=medical_record,
            run_id=run_id,
            run_key=run_key,
            started=started,
            completed_steps=completed_steps,
            failed_step=failed_step,
            errors=errors,
        )

    def _finish(
        self,
        *,
        medical_record: dict[str, Any],
        run_id: str,
        run_key: str,
        started: datetime,
        completed_steps: list[str],
        failed_step: str | None,
        errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        completed = datetime.now(timezone.utc)
        case_status = medical_record.get("case_status", "ERROR")
        if case_status == "REFERRED":
            status = "COMPLETE"
        elif case_status == "FOLLOW_UP":
            status = "COMPLETE_WITH_FOLLOW_UP"
        elif case_status == "DIAGNOSED":
            status = "COMPLETE_WITHOUT_REFERRAL"
        else:
            status = "FAILED"

        final_diagnoses = medical_record.get("final_diagnoses", [])
        referrals = medical_record.get("referrals", [])

        result = ClinicalPipelineResult(
            pipeline_run_id=run_id,
            case_id=medical_record["case_id"],
            medical_record_id=medical_record["medical_record_id"],
            status=status,
            started_at=started,
            completed_at=completed,
            completed_steps=tuple(completed_steps),
            failed_step=failed_step,
            final_diagnosis_id=(
                final_diagnoses[-1]["diagnosis_id"] if final_diagnoses else None
            ),
            referral_id=referrals[-1]["referral_id"] if referrals else None,
            case_status=case_status,
            errors=tuple(errors),
        )
        data = result.to_dict()

        self.event_log.append(
            medical_record,
            event_type="CLINICAL_PIPELINE_COMPLETED",
            payload={"pipeline_result": data},
            occurred_at=completed,
            idempotency_key=f"{run_key}:pipeline",
        )
        medical_record.setdefault("pipeline_runs", []).append(data)
        medical_record.setdefault("counters", {})["pipeline_run_count"] = len(
            medical_record["pipeline_runs"]
        )
        medical_record["updated_at"] = completed.isoformat()
        return data

    @staticmethod
    def _find_existing(
        medical_record: dict[str, Any], run_key: str
    ) -> dict[str, Any] | None:
        idempotency_key = f"{run_key}:pipeline"
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "CLINICAL_PIPELINE_COMPLETED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["pipeline_result"]
        return None
