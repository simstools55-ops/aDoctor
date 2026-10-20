# SBM Orchestrated Specialist Handoff v1.1.2

## 正式ワークフロー

`SBM → Doctor → SBM → Writer / Creator / Merge → SBM`

Doctorは診断と治療方針決定を担当し、専門製品への最終紹介状は作成しない。DoctorはSBM登録用の機械可読診断結果を返す。SBMは最初の診断依頼時に保持した記事本文、検索クエリ、内部リンク候補、改善履歴とDoctor診断を統合し、次の担当製品へ渡す完全な紹介状を生成する。

## 理由

Doctorから専門製品へ直接渡す短い依頼文だけでは、WriterがBeforeを確定するための記事本文や、判断に必要なクエリ・履歴が不足する可能性がある。カルテを保持するSBMが紹介状を生成することで、責務分離と情報完全性を両立する。

## 利用者操作

1. SBMの精密診断ダイアログ上段からDoctor依頼JSONをコピーする。
2. Doctorへ貼り付ける。
3. Doctor回答末尾のSBM登録用診断結果JSONだけをコピーする。
4. 同じダイアログ下段へ貼り付けて登録する。
5. SBMが即時表示するWriter / Creator / Merge紹介状をコピーする。
