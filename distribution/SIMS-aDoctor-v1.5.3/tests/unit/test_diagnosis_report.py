from pathlib import Path
import json

from src.doctor.reporting import DiagnosisReportBuilder


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/output/confirmed_writer_case.json").read_text(encoding="utf-8")
    )


def test_builds_user_facing_report_without_internal_rule_names():
    report = DiagnosisReportBuilder().build(load())
    assert "鮮度" in report["headline"]
    assert "CONTENT_STALE" not in json.dumps(report, ensure_ascii=False)
    assert report["reasons"]
