from doctor.clinical_review import (
    ClinicalFinding,
    ClinicalFindingCode,
    apply_low_sample_safety,
)
from doctor.confidence_scoring import ConfidenceFactors, calculate_confidence
from doctor.evidence_quality import (
    AcquisitionQuality,
    ContentQuality,
    EvidenceQualityAssessment,
)
from doctor.external_factors import DemandHealth, ExternalFactor, ExternalFactorType


def test_low_sample_does_not_block_factual_correction():
    result = apply_low_sample_safety(
        low_sample=True,
        findings=(
            ClinicalFinding(
                code=ClinicalFindingCode.FACTUAL_CORRECTION_REQUIRED,
                summary_ja="公式情報と一致しない記述があります。",
                confidence=95,
                requires_immediate_correction=True,
            ),
        ),
    )
    assert result.correction_required is True
    assert result.status == "CORRECTION_REQUIRED"
    assert result.low_sample_override_applied is True


def test_evidence_acquisition_and_content_quality_are_separate():
    item = EvidenceQualityAssessment(
        evidence_id="E007",
        acquisition_quality=AcquisitionQuality.VALID,
        content_quality=ContentQuality.LOW,
        note_ja="候補は取得できましたが関連性が低いです。",
    )
    assert item.usable is True
    assert item.to_dict()["content_quality"] == "LOW"


def test_confidence_is_derived_from_factors():
    score = calculate_confidence(
        ConfidenceFactors(
            evidence_score=100,
            low_sample=True,
            missing_serp=True,
            conflicting_signals=True,
        )
    )
    assert score == 60


def test_external_demand_can_exclude_improvement_failure():
    factor = ExternalFactor(
        factor_type=ExternalFactorType.OFFICIAL_EVENT,
        demand_health=DemandHealth.COLLAPSED,
        confidence=90,
        source_type="OFFICIAL_ANNOUNCEMENT",
        source_label="自治体公式発表",
        observed_at="2026-08-05",
        summary_ja="配布完了により検索需要が縮小しました。",
    )
    assert factor.excludes_improvement_failure() is True
