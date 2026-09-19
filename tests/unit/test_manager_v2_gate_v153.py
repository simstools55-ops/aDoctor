from doctor.receiver.manager_v2_gate import validate_manager_v2_gate

def valid():
    return {"format":"SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2","contract_version":"2.0","schema_version":"2.0.0","source_system":"SIMS_BLOG_MANAGER","target_system":"SIMS_DOCTOR","case_id":"CASE-1","request":{"request_id":"REQ-1"},"site":{"site_id":"SITE-1"},"article":{"article_id":"A1"}}

def test_valid_manager_v2_passes(): assert validate_manager_v2_gate(valid()) == (True,"OK")
def test_free_form_shape_fails(): assert validate_manager_v2_gate({"prompt":"診断して"})[0] is False
def test_old_envelope_only_fails(): assert validate_manager_v2_gate({"PROTOCOL":"SIMS-A/1"})[0] is False
def test_wrong_source_fails():
    p=valid(); p["source_system"]="OTHER"; assert validate_manager_v2_gate(p)[0] is False
def test_missing_id_fails():
    p=valid(); p["request"]["request_id"]=""; assert validate_manager_v2_gate(p)[0] is False
