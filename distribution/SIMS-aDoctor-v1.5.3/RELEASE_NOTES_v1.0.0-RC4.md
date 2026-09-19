# SIMS Doctor v1.0.0 RC4

## 目的
実記事受入試験で確認された、検索データだけでは発見できない本文矛盾・誤情報・鮮度問題を診断フローへ正式に追加する。

## 主な変更
- Clinical Review（本文診断）を追加
- LOW_SAMPLEは大規模SEO変更のみを抑止し、事実修正は許可
- SEO・本文・SERP・外部要因・Workflowを並列評価する複合診断へ拡張
- Evidenceの取得品質と内容品質を分離
- Evidence Confidence Scoringを追加
- 外部需要変動と改善失敗を切り分けるルールを追加
- `WAIT_FOR_EFFECT_MEASUREMENT`、`WAIT_FOR_MORE_EVIDENCE`、`MONITOR_ONLY`、`LIMITED_CONTENT_REPAIR`を区別
- 利用者向け本文は日本語のみ。内部コードはJSON・Trace・QAに限定

## 後方互換
既存の `SIMS_DOCTOR_SINGLE_CASE_RESULT_V1` contract_version 1.0を維持し、追加フィールドは1.1として任意拡張する。
