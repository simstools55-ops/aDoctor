from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

def test_release_manifest_contracts_exist():
    manifest = json.loads(
        (ROOT / "product/Release/RELEASE_MANIFEST_v1.0.0-RC1.json")
        .read_text(encoding="utf-8")
    )
    for name in manifest["contracts"]:
        assert (ROOT / "contracts" / name).exists()

def test_release_manifest_events_match_registry():
    manifest = json.loads(
        (ROOT / "product/Release/RELEASE_MANIFEST_v1.0.0-RC1.json")
        .read_text(encoding="utf-8")
    )
    events = json.loads(
        (ROOT / "knowledge/workflow/medical_record_events.json")
        .read_text(encoding="utf-8")
    )
    assert set(manifest["medical_record_events"]).issubset(set(events["items"]))

def test_version_is_release_candidate():
    assert (ROOT / "VERSION").read_text(
        encoding="utf-8"
    ).strip() == "1.4.0"

def test_treatment_execution_remains_disabled():
    manifest = json.loads(
        (ROOT / "product/Release/RELEASE_MANIFEST_v1.0.0-RC1.json")
        .read_text(encoding="utf-8")
    )
    assert manifest["responsibility"]["treatment_execution"] is False
