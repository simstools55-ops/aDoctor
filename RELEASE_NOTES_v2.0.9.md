# aDoctor v2.0.9 UAT

- SBM v9.3.8の精密診断（診断依頼・処置決定依頼）見出しと「別途確認する課題ID」を受理。旧名称も維持。
- `SIMS_STRATEGY_DOCTOR_V1` の既存8項目、4区分、記事別actions契約は不変。
- 通常改善の追加診断 `SIMS_FOLLOWUP_DOCTOR_V1` を第4受付経路として追加。
- 現行Managerは追加診断にCaseID/RequestIDを出力しないため、この経路に限り記事ID・URL・診断事項・初回Writer回答を受付条件とする。
- 通常V2、情報変更、記事の公開・登録は変更しない。
- JSONの形は静的検証済み。Claude実機での受付試験は未実施。
