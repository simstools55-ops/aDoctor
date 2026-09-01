from __future__ import annotations

from typing import Any, Dict, Optional

from doctor.common.errors import DoctorError


def success_result(
    status: str, completed_at: str, request_id: str, case_id: str,
    medical_record_id: str, case_status: str,
) -> Dict[str, Any]:
    message = (
        "同じ記事の診療中カルテが存在するため、既存Caseへ依頼を追加しました。"
        if status == "EXISTING_CASE_REUSED"
        else "診断依頼を受け付け、カルテを作成しました。"
    )
    return {
        "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
        "contract_version": "1.0",
        "status": status,
        "completed_at": completed_at,
        "request_id": request_id,
        "case_id": case_id,
        "medical_record_id": medical_record_id,
        "case_status": case_status,
        "message": message,
        "error": None,
    }


def error_result(error: DoctorError, completed_at: str) -> Dict[str, Any]:
    return {
        "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
        "contract_version": "1.0",
        "status": "REJECTED",
        "completed_at": completed_at,
        "request_id": None,
        "case_id": None,
        "medical_record_id": None,
        "case_status": None,
        "message": "診断依頼を受け付けられませんでした。入力内容を確認してください。",
        "error": {"code": error.code, "message": error.message, "field": error.field},
    }
