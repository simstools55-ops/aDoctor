# SIMS Article Doctor v1.4.0

- `SIMS_DOCTOR_CASE_RESULT_V2` に任意の `knowledge_candidates` を追加。
- SBMから受け取る `personal_knowledge_site_id` を結果へ引き継ぐ。
- Doctorは再利用可能な記事役割・意図境界・カニバリ境界・鮮度リスク等のみ候補化し、現在順位・クリック・SERPスナップショット等の一時情報は候補化しない。
- 候補の最終採否・永続化はSBM Knowledge Writerが担当する。
- 既存 `SIMS_DOCTOR_*` 契約は維持し、候補なしの結果も有効。
