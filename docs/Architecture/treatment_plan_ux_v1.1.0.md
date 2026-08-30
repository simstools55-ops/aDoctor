# SIMS Article Doctor v1.1.0 Treatment Plan UX Standard

## Purpose
Doctorの回答はSEOレポートではなく、利用者が安心して次の行動へ進むための治療計画書です。

## Required order
1. Article Doctorコメント
2. 総合診断（診断、確信度、治療区分、次の担当）
3. 今回やること
4. 今回はやらないこと
5. この方針にした理由
6. 利用者へのアドバイス
7. Writer / Creator / Mergeへのコピー専用依頼文
8. SBMで行うこと
9. 次回診察予定

## Confidence policy
- 95%以上: ほぼ確定。Doctorが方針を決定する。
- 80〜94%: 可能性が高い。利用者へ分析を委ねず、Doctorが方針を決定する。
- 60〜79%: 有力な推定。低リスク処置を優先し、必要最小限の確認だけ依頼できる。
- 40〜59%: 追加証拠が望ましい。大規模処置を止める。
- 40%未満: 診断保留。

## Reassurance
安心コメントは根拠のない楽観ではありません。重大な問題がない場合、慌てて全面リライト、URL変更、削除を行う必要がないことを明確にします。

## User workload
SEO分析、サイト横断比較、原因切り分けを利用者へ丸投げしません。Doctorが利用可能な証拠から判断します。利用者確認は、Search Console URL検査などDoctorが実行できない検査で、かつ治療分岐に不可欠な場合だけです。

## Copy-ready handoff
担当製品への依頼文は独立したプレーンテキストコードブロックとして表示します。説明文、診断JSON、コピー対象外の注記を混在させません。

## JSON
通常利用者向け回答にDoctor診断JSONを表示しません。SBMへ登録するのはWriter / Creator / Mergeが処置完了後に返す結果JSONだけです。
