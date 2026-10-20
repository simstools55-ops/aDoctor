# aDoctor v1.5.3 / SBM9 記事内容更新 UAT

この版は正式配布前の試験版です。通常診断を維持したまま、SBM9記事内容変更・更新依頼の受付を追加します。

1. Claudeプロジェクトの現行InstructionsとKnowledgeをバックアップします。
2. `Claude-Upload`パッケージの`CLAUDE_PROJECT_INSTRUCTIONS.md`全文をプロジェクト指示に設定します。
3. `Knowledge/`、`contracts/`、`Runtime/`、`shared/`、`Examples/`（存在するもの）および版・契約マニフェストをプロジェクトKnowledgeへ登録します。指示書をKnowledgeへ重複登録しません。
4. SBMからの「記事内容の変更・更新」依頼を投入し、`SIMS_INFO_CHANGE_DOCTOR_RESPONSE_V1`形式を確認します。
5. 通常の`SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2`が従来どおり受理されることを確認します。

公式根拠が得られない場合は`NEEDS_EVIDENCE`とし、利用者に追加資料登録・再診を要求する標準手順を作りません。公開・更新操作は行いません。
