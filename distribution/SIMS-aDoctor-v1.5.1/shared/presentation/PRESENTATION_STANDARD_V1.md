# SIMS Presentation Standard v1

## Standard order
利用者向けの主要出力は、原則として次の順序で提示する。

1. 公開可否または実行可否
2. 今回やること
3. 変更内容または成果物
4. 理由と期待効果
5. 今回やらないこと / 注意事項（必要な場合のみ）
6. 次の作業
7. Machine JSON（利用者の運用上必要な場合のみ、最後に配置）

## Existing article treatment
Writerが変更を提示する場合、各変更は以下を満たす。
- target
- Before
- After
- reason
- expected_effect

Afterは、利用者が原則そのままコピーして記事へ反映できる完成形とする。
新規追加でBeforeが存在しない場合も省略せず「（該当箇所なし・新規追加）」等と明示する。

## No simplification for referral mode
DOCTOR_REFERRAL_TREATMENT等の経路であっても、通常Writerより利用者向け表示品質を下げてはならない。
治療範囲が狭いことは、Before/Afterや理由の省略理由にならない。

## Product-specific projection
- Doctor: 診断要約 / 今回やること / 今回やらないこと / 再診
- Writer: 公開可否 / Before / After / 理由 / 期待効果
- Creator: 記事作成結果 / 公開前確認 / 完成記事
- Merge: 統合判断 / Primary / Preservation / 作業順序 / 注意事項
- SBM: 次に実行すべき操作と状態を人間向けに表示
