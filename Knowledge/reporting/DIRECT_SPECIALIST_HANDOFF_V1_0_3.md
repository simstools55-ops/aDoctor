# Direct Specialist Handoff v1.0.3

## 正式フロー

SBM → Doctor → Writer / Creator / Merge → SBM

Doctorは診断後、対象製品への依頼文を利用者向け本文に必ず表示する。利用者はその依頼文を直接対象製品へ渡す。Doctor診断結果をSBMへ登録して同じ依頼文を再生成する運用は行わない。

## SBMの役割

- Doctor依頼の作成
- CaseIDの発行と保持
- Writer / Creator / Mergeの処置結果の登録
- 公開後の効果測定
- 再診予定の管理

Doctor診断JSONは監査・保管用の任意情報であり、通常運用では利用者が登録する必要はない。

## Doctor出力

1. 優先順位チェックリスト
2. 今回やること
3. 利用者が確認すること（結果別の次の行動を含む）
4. 対象製品へのコピー可能な依頼文
5. 診断結果と根拠
6. 再診条件
7. 診断記録JSON（通常操作不要）

Writer等への依頼文にはCaseID、ArticleID、実施範囲、禁止範囲、依存条件、および「処置結果をSBMへ登録する」指示を含める。
