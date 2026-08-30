from datetime import datetime, timezone

import pytest

from src.doctor.observation import Finding, ObservationEvent


def test_observation_event_keeps_facts_without_evaluation():
    event = ObservationEvent(
        observation_id="OBS-1",
        observation_type="SEARCH_CONSOLE",
        observed_at=datetime.now(timezone.utc),
        source="GSC",
        facts={"clicks": 10, "impressions": 1000, "ctr": 0.01, "position": 8.2},
    )
    assert event.facts["position"] == 8.2


def test_finding_confidence_range():
    with pytest.raises(ValueError):
        Finding(
            finding_id="FND-1",
            code="CTR_UNDERPERFORMING",
            severity="MODERATE",
            confidence=101,
            created_at=datetime.now(timezone.utc),
            evidence_ids=("EVD-1",),
            affected_period={"start": "2026-01-01", "end": "2026-01-28"},
            rule_version="1.0",
        )
