from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_protocol_spec_contains_required_envelope_fields():
    text = (ROOT / 'docs' / 'SIMS_REQUEST_PROTOCOL_V1.md').read_text(encoding='utf-8')
    for token in [
        'PROTOCOL=SIMS-A/1', 'SOURCE=SIMS_MANAGER', 'EDITION=FULL',
        'TARGET=ADOCTOR', 'REQUEST_TYPE=ARTICLE_DIAGNOSIS',
        'REQUEST_ID=', 'CASE_ID=', 'SITE_ID=', 'ARTICLE_ID='
    ]:
        assert token in text


def test_protocol_does_not_claim_license_or_crypto_authentication():
    text = (ROOT / 'docs' / 'SIMS_REQUEST_PROTOCOL_V1.md').read_text(encoding='utf-8')
    assert 'does not replace SIMS License Center' in text
    assert 'does not cryptographically authenticate Manager' in text
