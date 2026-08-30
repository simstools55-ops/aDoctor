from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.pipeline import ClinicalPipelineOrchestrator


class Fake:
    def __init__(self, method, result=None, side_effect=None):
        self.method = method
        self.result = result
        self.side_effect = side_effect

    def __getattr__(self, name):
        if name != self.method:
            raise AttributeError(name)

        def call(*args, **kwargs):
            if self.side_effect:
                raise self.side_effect
            return self.result

        return call


def record():
    return {
        "case_id": "CASE-1",
        "medical_record_id": "MR-1",
        "events": [],
        "pipeline_runs": [],
        "final_diagnoses": [],
        "referrals": [],
        "counters": {"pipeline_run_count": 0},
        "case_status": "READY_FOR_OBSERVATION",
    }


def orchestrator(referral_error=None):
    log = MedicalRecordEventLog({"CLINICAL_PIPELINE_COMPLETED"})
    return ClinicalPipelineOrchestrator(
        event_log=log,
        evidence_engine=Fake("extract_all", []),
        vital_signs_engine=Fake("calculate", {}),
        findings_engine=Fake("generate_all", []),
        differential_engine=Fake("assess", {}),
        final_diagnosis_engine=Fake("confirm", {}),
        treatment_engine=Fake("recommend", {}),
        referral_engine=Fake("issue", {}, referral_error),
        policy={},
    )


def test_pipeline_fails_when_all_observations_fail():
    item = record()
    result = orchestrator().run(
        item,
        run_key="run:1",
        observation_callbacks={
            "SEARCH_CONSOLE_OBSERVATION": lambda: (_ for _ in ()).throw(ValueError("fail")),
            "SERP_OBSERVATION": lambda: (_ for _ in ()).throw(ValueError("fail")),
            "ARTICLE_SNAPSHOT_OBSERVATION": lambda: (_ for _ in ()).throw(ValueError("fail")),
        },
    )
    assert result["status"] == "FAILED"
    assert result["failed_step"] == "OBSERVATION"
    assert item["case_status"] == "ERROR"


def test_pipeline_reuses_completed_result():
    item = record()

    def diagnosis():
        item["final_diagnoses"].append({"diagnosis_id": "DX-1"})
        item["case_status"] = "DIAGNOSED"

    def referral():
        item["referrals"].append({"referral_id": "REF-1"})
        item["case_status"] = "REFERRED"

    pipe = ClinicalPipelineOrchestrator(
        event_log=MedicalRecordEventLog({"CLINICAL_PIPELINE_COMPLETED"}),
        evidence_engine=Fake("extract_all", []),
        vital_signs_engine=Fake("calculate", {}),
        findings_engine=Fake("generate_all", []),
        differential_engine=Fake("assess", {}),
        final_diagnosis_engine=Fake("confirm", side_effect=None),
        treatment_engine=Fake("recommend", {}),
        referral_engine=Fake("issue", {}),
        policy={},
    )
    pipe.final_diagnosis_engine.confirm = lambda *a, **k: diagnosis()
    pipe.referral_engine.issue = lambda *a, **k: referral()

    callbacks = {"SEARCH_CONSOLE_OBSERVATION": lambda: {}}
    first = pipe.run(item, run_key="run:2", observation_callbacks=callbacks)
    second = pipe.run(item, run_key="run:2", observation_callbacks=callbacks)
    assert first["pipeline_run_id"] == second["pipeline_run_id"]
    assert len(item["pipeline_runs"]) == 1
