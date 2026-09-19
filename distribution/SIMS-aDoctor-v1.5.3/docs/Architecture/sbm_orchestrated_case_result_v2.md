# SBM-Orchestrated Case Result V2

The standard RC12 route is:

```text
SBM -> Doctor -> SBM -> Writer -> SBM
```

SBM owns CaseID, workflow state, history, publication tracking, measurement, and reexamination scheduling. Doctor performs diagnosis and returns a treatment plan and referral recommendation. Doctor does not directly invoke Writer, Creator, or Merge.

The standard return contract is `SIMS_DOCTOR_CASE_RESULT_V2` version `2.0`.

Legacy direct specialist request builders are retained only for backward compatibility.


### Site Diagnosis Identity Contract Hotfix (v1.3.0)
Site Diagnosis 由来の案件では、SBM が発行した識別情報を診断内容と同様に正本として扱い、出力時に変更・再生成・ネスト化しない。

`SIMS_DOCTOR_CASE_RESULT_V2` のトップレベルへ、次の7項目を必ず出力する。
- `case_id`
- `request_id`
- `site_diagnosis_case_id`
- `site_diagnosis_batch_id`
- `site_id`
- `article_id`
- `article_url`

Site Diagnosis ケースでは `site_diagnosis_case_id` と `site_diagnosis_batch_id` を省略してはならない。入力パッケージに存在する値をそのまま継承する。再診断・再検証・JSON再出力でも同じIdentityを保持する。`case_identity` 等の独自オブジェクトへ移動・ネストしてはならない。

値が確認できない場合は推測・生成せず、SBM登録用JSONを完成扱いにしない。利用者へ「Site Diagnosis識別情報が入力パッケージから確認できない」と明示して、元のケースパッケージの確認を求める。

通常の個別診断（Site Diagnosis由来でない案件）では、存在しない `site_diagnosis_case_id` / `site_diagnosis_batch_id` を捏造しない。
