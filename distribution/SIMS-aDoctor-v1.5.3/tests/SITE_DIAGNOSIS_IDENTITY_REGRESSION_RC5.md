# Site Diagnosis Identity Contract Regression Test

PASS条件:
1. Site Diagnosis入力の7識別子が結果JSONトップレベルに存在する。
2. 値は入力と完全一致する。
3. `case_identity` を生成しない。
4. 再診断でも7識別子が維持される。
5. 診断・治療方針の意味内容はIdentity修正により変化しない。
