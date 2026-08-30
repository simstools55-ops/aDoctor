# SIMS Doctor v1.1.2 Release Notes

## 目的
SBM 5.9.8の一画面Doctor連携に合わせ、Doctor診断結果をSBMへ必須返却するワークフローへ統一しました。

## 変更
- DoctorからWriter / Creator / Mergeへの直接依頼文を通常出力から削除
- 回答末尾のSBM登録用診断結果JSONを復活
- `workflow.return_to` を `SIMS_BLOG_MANAGER` に変更
- SBMが記事本文・クエリ・内部リンク候補・履歴を統合して専門製品紹介状を生成
- URL正規化診断ルールはv1.1.1から継承
