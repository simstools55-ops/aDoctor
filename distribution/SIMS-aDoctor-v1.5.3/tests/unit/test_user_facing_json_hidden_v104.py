from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_v104_policy_exists():
    text=(ROOT/'docs/Architecture/user_facing_json_hidden_v1.0.4.md').read_text(encoding='utf-8')
    assert '利用者向け回答にDoctor結果JSONを表示しない' in text
    assert 'SIMS Writerへそのまま貼り付けてください' in text
