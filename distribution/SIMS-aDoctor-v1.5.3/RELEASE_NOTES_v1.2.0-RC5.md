# SIMS Doctor v1.2.0-RC5

## Site Diagnosis Identity Contract Hotfix

- Site Diagnosis案件の `case_id`, `request_id`, `site_diagnosis_case_id`, `site_diagnosis_batch_id`, `site_id`, `article_id`, `article_url` をトップレベルで不変継承する規則を追加。
- `case_identity` 等への独自ネストを禁止。
- 再診断・再検証・JSON再出力でもIdentityを保持。
- Identity不足時は推測生成せず、SBM登録用JSONを完成扱いにしない。
- 診断ロジック、Treatment Strategy、Confidence、Writer/Creator/Mergeへのルーティングは変更なし。
