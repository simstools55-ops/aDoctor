import json
from pathlib import Path
from runtime.catalog_importer import validate_catalog, create_collector_job, CatalogValidationError

def sample():
    p=Path(__file__).parents[1]/"contracts"/"examples"/"article-catalog.example.json"
    return json.loads(p.read_text(encoding="utf-8"))

def test_valid_catalog_creates_ready_job():
    payload=sample(); validate_catalog(payload); job=create_collector_job(payload)
    assert job.status=="READY"
    assert job.site_id==payload["site"]["site_id"]

def test_duplicate_article_id_rejected():
    payload=sample(); payload["articles"].append(dict(payload["articles"][0])); payload["catalog"]["article_count"]=2
    try: validate_catalog(payload)
    except CatalogValidationError: return
    assert False, "duplicate must be rejected"
