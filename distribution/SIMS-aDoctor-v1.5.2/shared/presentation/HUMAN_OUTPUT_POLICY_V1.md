# SIMS Human Output Policy v1

## Show to users
利用者向け出力は、作業に必要な情報を優先する。
- 公開可否 / 実行可否
- 今回やること
- Before / After（変更作業がある場合）
- 理由
- 期待効果
- 注意事項
- 次の作業
- 再診・測定予定（必要な場合）

## Do not expose by default
次の情報はMachine Layerに保持し、利用者への通常説明には出さない。
- Contract名・schema詳細
- allowed_scope / blocked_scope等の内部フィールド名
- Routing / handoff_mode
- Internal Flags
- Evidence IDの羅列
- Confidenceの内部計算過程
- Adapterのフォールバック処理
- 「空配列なので別フィールドを正本とみなす」等の内部整合処理

必要な意味は自然な日本語へ変換する。
例: `FULL_REWRITE`をそのまま説明するのではなく「今回は全面リライトを行いません」と提示する。

## Human usability requirement
正しいMachine JSONが存在するだけでは品質合格としない。利用者がHuman Outputだけで次の作業を開始できることを必要条件とする。
