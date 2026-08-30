from datetime import datetime, timezone

from doctor.common.clock import Clock
from doctor.output import CaseResultV2Builder
from doctor.service import DoctorReceptionService


class FixedClock(Clock):
    def now(self):
        return datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc)


def sbm_v2_request():
    return {
        "format": "SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2",
        "contract_version": "2.0",
        "schema_version": "2.0.0",
        "generated_at": "2026-08-05T15:00:00+09:00",
        "case_id": "CASE-20260805-A999999-001",
        "site": {
            "site_id": "sample-site",
            "site_name": "サンプルブログ",
            "blog_url": "https://example.com/"
        },
        "request": {
            "request_id": "REQ-1",
            "requested_at": "2026-08-05T15:00:00+09:00",
            "source_sheet": "記事管理",
            "chief_complaint": "個別診断"
        },
        "article": {
            "article_id": "A999999",
            "url": "https://example.com/article",
            "title": "記事タイトル"
        },
        "workflow": {
            "lock": {"locked": False}
        }
    }


def test_sbm_v2_case_id_is_preserved():
    result = DoctorReceptionService(clock=FixedClock()).accept(sbm_v2_request())
    assert result["status"] == "ACCEPTED"
    assert result["case_id"] == "CASE-20260805-A999999-001"


def test_case_result_v2_hands_off_directly_and_returns_specialist_result_to_sbm():
    record = {
        "case_id": "CASE-1",
        "medical_record_id": "MR-CASE-1",
        "patient": {"site_id": "site", "article_id": "A1"},
        "final_diagnoses": [{
            "diagnosis_id": "D1", "status": "CONFIRMED",
            "diagnosis_code": "CONTENT_STALE", "confidence": "HIGH",
            "severity": "MEDIUM", "evidence_ids": ["E1"]
        }],
        "treatment_recommendations": [{
            "target": "WRITER", "treatment_code": "LIMITED_REPAIR",
            "priority": "HIGH", "recommended_scope": ["summary"],
            "prohibited_actions": ["full_body_rewrite"],
            "monitoring": {"review_after_days": 28}
        }],
        "referrals": [{"target": "WRITER", "referral_id": "R1"}]
    }
    result = CaseResultV2Builder().build(record)
    assert result["format"] == "SIMS_DOCTOR_CASE_RESULT_V2"
    assert result["referral"]["destination"] == "SIMS_WRITER"
    assert result["workflow"]["return_to"] == "SIMS_BLOG_MANAGER"
    assert result["workflow_handoff"]["specialist_result_destination"] == "SIMS_BLOG_MANAGER"
    assert result["compatibility"]["direct_specialist_invocation"] == "DISABLED"
