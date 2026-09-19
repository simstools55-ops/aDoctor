def execute(item, case_id, run_key):
    return {
        "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
        "result_status": "DIAGNOSED",
        "case_id": case_id,
        "referral": {"target": "WRITER"},
    }
