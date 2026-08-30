import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_identity_and_versions():
    assert (ROOT/'VERSION').read_text().strip() == '1.4.0'
    assert (ROOT/'SHARED_VERSION').read_text().strip() == '3.5.0'
    identity=json.loads((ROOT/'PRODUCT_IDENTITY.json').read_text())
    assert identity['product_code']=='DOCTOR'
    assert identity['repository_name']=='SIMS-Article-Doctor'

def test_platform_contracts_exist_and_parse():
    for name in ['SIMS_DOCTOR_DIAGNOSIS_REQUEST_V1.schema.json','SIMS_DOCTOR_DIAGNOSIS_RESULT_V1.schema.json','SIMS_PLATFORM_ERROR_V1.schema.json']:
        data=json.loads((ROOT/'contracts/platform'/name).read_text())
        assert '$schema' in data

def test_snapshot_manifest():
    m=json.loads((ROOT/'shared/SNAPSHOT_MANIFEST.json').read_text())
    assert m['shared_version']=='3.5.0'
    assert m['snapshot_for']=='DOCTOR'

def test_no_direct_treatment_invocation_in_rc13_doc():
    text=(ROOT/'docs/PLATFORM_CONTRACT_ADAPTATION_RC13.md').read_text()
    assert 'does not invoke Writer, Creator, or Merge directly' in text
