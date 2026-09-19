from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def text(): return (ROOT/'docs'/'SIMS_REQUEST_PROTOCOL_V1.md').read_text(encoding='utf-8')

def test_protocol_uses_manager_v2_contract():
    t=text()
    for token in ['SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2','contract_version','2.0','schema_version','2.0.0','SIMS_BLOG_MANAGER','SIMS_DOCTOR','request.request_id','site.site_id','article.article_id']:
        assert token in t

def test_protocol_rejects_obsolete_wrapper_and_free_form():
    t=text(); assert 'Do not require a second `[SIMS_REQUEST]` wrapper' in t; assert 'free-form diagnosis prompts' in t

def test_protocol_does_not_claim_license_or_crypto_authentication():
    t=text(); assert 'not a license check' in t; assert 'not cryptographic authentication' in t
