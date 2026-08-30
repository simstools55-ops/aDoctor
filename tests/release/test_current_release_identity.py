import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = '1.4.0'


def test_current_release_identity_is_consistent():
    assert (ROOT / 'VERSION').read_text(encoding='utf-8').strip() == EXPECTED
    identity = json.loads((ROOT / 'PRODUCT_IDENTITY.json').read_text(encoding='utf-8'))
    assert identity['current_version'] == EXPECTED
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert f'## Current release\n\n`{EXPECTED}`' in readme
