from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcquisitionQuality(str, Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"
    EMPTY = "EMPTY"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class ContentQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_ASSESSED = "NOT_ASSESSED"


@dataclass(frozen=True)
class EvidenceQualityAssessment:
    evidence_id: str
    acquisition_quality: AcquisitionQuality
    content_quality: ContentQuality
    note_ja: str

    @property
    def usable(self) -> bool:
        return self.acquisition_quality in {
            AcquisitionQuality.VALID,
            AcquisitionQuality.WARNING,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "acquisition_quality": self.acquisition_quality.value,
            "content_quality": self.content_quality.value,
            "usable": self.usable,
            "note_ja": self.note_ja,
        }
