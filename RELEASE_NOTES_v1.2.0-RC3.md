# SIMS Doctor v1.2.0-RC3

## Human Experience / Presentation Framework
- Shared Editorial Knowledge 3.5.0へ同期。
- `presentation` を `SIMS_DOCTOR_CASE_RESULT_V2` に追加。
- Human Layerは診断要約、今回やること、今回やらないこと、次の作業、再診目安に限定。
- Contract / Routing / Scope等のMachine情報は既存フィールドに保持し、Presentationへ露出しない。
- Doctor ReferralのMachine Contractは変更せず、SBMが専門家紹介状を生成する責務を維持。
- Human Usability Gate回帰テストを追加。
