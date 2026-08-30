from pathlib import Path

from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.evidence import EvidenceEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.findings import FindingsEngine
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.pipeline import ClinicalPipelineOrchestrator
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine
from src.doctor.vital_signs import VitalSignsEngine


ROOT = Path(__file__).resolve().parents[2]


def test_pipeline_runs_from_existing_observations_to_referral():
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "patient": {
            "site_id": "site",
            "article_id": "A1",
            "article_url": "https://example.com/a",
            "article_title": "Article",
        },
        "events": [],
        "observations": [{
            "observation_id": "OBS-20260804-120000-ABCDEF",
            "observation_type": "SEARCH_CONSOLE",
            "observed_at": "2026-08-04T12:00:00+00:00",
            "source": "GOOGLE_SEARCH_CONSOLE",
            "schema_version": "1.0",
            "facts": {
                "periods": {
                    "days_28": {"clicks": 5, "impressions": 1000, "ctr": 0.005, "position": 8.0},
                    "days_90": {"clicks": 20, "impressions": 3200, "ctr": 0.00625, "position": 8.0},
                    "days_365": {"clicks": 80, "impressions": 12000, "ctr": 0.0067, "position": 8.0}
                },
                "queries": [],
                "retrieval": {},
            },
        }],
        "evidence": [],
        "vital_profiles": [],
        "findings": [],
        "differential_assessments": [],
        "final_diagnoses": [],
        "treatment_recommendations": [],
        "referrals": [],
        "pipeline_runs": [],
        "history": [],
        "counters": {
            "evidence_count": 0,
            "vital_profile_count": 0,
            "finding_count": 0,
            "differential_count": 0,
            "final_diagnosis_count": 0,
            "treatment_recommendation_count": 0,
            "referral_count": 0,
            "pipeline_run_count": 0,
        },
        "case_status": "OBSERVING",
        "updated_at": "2026-08-04T12:00:00+00:00",
    }

    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    allowed = {
        "EVIDENCE_RECORDED", "VITAL_SIGNS_CALCULATED", "FINDING_RECORDED",
        "DIFFERENTIAL_UPDATED", "FINAL_DIAGNOSIS_CONFIRMED",
        "TREATMENT_RECOMMENDED", "REFERRAL_ISSUED",
        "CLINICAL_PIPELINE_COMPLETED"
    }
    log = MedicalRecordEventLog(allowed)
    pipe = ClinicalPipelineOrchestrator(
        event_log=log,
        evidence_engine=EvidenceEngine(ckb, log),
        vital_signs_engine=VitalSignsEngine(ckb, log),
        findings_engine=FindingsEngine(ckb, log),
        differential_engine=DifferentialDiagnosisEngine(ckb, log),
        final_diagnosis_engine=FinalDiagnosisEngine(ckb, log),
        treatment_engine=TreatmentRecommendationEngine(ckb, log),
        referral_engine=ReferralEngine(ckb, log),
        policy=ckb.pipeline_policy(),
    )

    result = pipe.run(
        record,
        run_key="integration:1",
        observation_callbacks={
            "SEARCH_CONSOLE_OBSERVATION": lambda: record["observations"][0]
        },
    )

    assert result["status"] in {"COMPLETE", "COMPLETE_WITH_FOLLOW_UP"}
    assert record["pipeline_runs"]
    assert any(event["event_type"] == "CLINICAL_PIPELINE_COMPLETED" for event in record["events"])
