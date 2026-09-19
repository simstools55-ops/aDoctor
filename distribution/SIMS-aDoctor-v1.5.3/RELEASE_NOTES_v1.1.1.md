# SIMS Doctor v1.1.1 Release Notes

## Theme
URL Identity / Canonical Diagnostic Accuracy

## Changes
- 末尾スラッシュ有無を同一ページ候補として扱うURL Identity判定を追加
- Search Console `matched_url`、canonical、Google選択正規URL、リダイレクト先を総合評価
- 非正規URLが未登録でも、正規URLが登録済みならインデックス消失と誤診しない
- 技術的インデックス障害と検索評価低下を明確に分離
- 利用者にスラッシュ選択を求めず、必要時はGoogle選択正規URLだけを確認依頼
- 回帰テストを追加

Treatment Plan UX、直接専門製品引き継ぎ、利用者向けJSON非表示は維持します。
