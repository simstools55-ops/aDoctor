# SIMS 特別改善連携契約 UAT v0.1.0（実装前の仕様正本）

## 範囲
Manager v7.1.12 / aDoctor v1.5.3 / aWriter v4.0.0。aMerge対象外。通常改善の契約と履歴は不変。

## 既存案件の互換性
既存 `SIMS_EMERGENCY_DOCTOR_REQUEST_V1` を受理する。`request_id`, `case_id`, `article_id`, `article_url` を依頼と回答で厳密一致。Manager発行の既存CaseIDを変更・再受付しない。

## Doctor回答
`format=SIMS_EMERGENCY_DOCTOR_RESULT_V1`、ID4項目、`decision` は `CHANGE_REQUIRED` / `NO_CHANGE` / `INSUFFICIENT_EVIDENCE`。`findings` は配列。`CHANGE_REQUIRED` のときのみ1件以上、各要素に非空 `change` とHTTPS `source_url` が必須。その他は空配列を許容。`reason` は非空。証拠不足を変更事実として捏造しない。実在する変更のみ一次情報で検証。

## 分岐
`CHANGE_REQUIRED` の場合だけWriter依頼へ。`NO_CHANGE` は「修正不要として終了」、`INSUFFICIENT_EVIDENCE` は「根拠不足で保留」の独立した状態を使用。いずれも「公開済み」と表示しない。根拠不足から再診する際は同じCaseIDで新たな診断依頼の履歴を追記する設計とし、原本を上書きしない。

## Writer依頼
`format=SIMS_EMERGENCY_WRITER_REQUEST_V1`、ID4項目、元のDoctor回答、修正対象・出典、編集範囲、公開禁止の明記を必須。Doctorの `decision=CHANGE_REQUIRED` の場合のみ受理。

## Writer回答
`format=SIMS_EMERGENCY_WRITER_RESULT_V1`、ID4項目、`revised_article`（100文字以上）、`change_summary`（非空）、`publication_status=NOT_PUBLISHED`。記事本文を渡していない場合は全文完成稿を捏造しない。原稿未提供時は不足資料を明示し、Managerは公開待ちへ進めない。

## 公開ゲート
実公開と公開ページの利用者確認を要件とする。UATの模擬公開は別の試験専用状態とし、本番の公開実績を記録しない。

## 安全性
通常Doctor V2、通常Writer Treatment V1、通常改善テキスト形式のゲートは維持。専用形式の受付は追加分岐とする。JSON上のsource_system等は暗号学的な真正性を保証しない。
