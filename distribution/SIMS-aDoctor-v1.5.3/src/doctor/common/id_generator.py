from __future__ import annotations

from datetime import datetime
import secrets
from typing import Protocol


class SequenceProvider(Protocol):
    def next_case_sequence(self, date_key: str) -> int: ...


def generate_request_id(now: datetime) -> str:
    suffix = secrets.token_hex(3).upper()
    return f"DREQ-{now.strftime('%Y%m%d-%H%M%S')}-{suffix}"


def generate_case_id(now: datetime, sequence_provider: SequenceProvider) -> str:
    date_key = now.strftime('%Y%m%d')
    sequence = sequence_provider.next_case_sequence(date_key)
    return f"CASE-{date_key}-{sequence:06d}"


def medical_record_id(case_id: str) -> str:
    return f"MR-{case_id}"
