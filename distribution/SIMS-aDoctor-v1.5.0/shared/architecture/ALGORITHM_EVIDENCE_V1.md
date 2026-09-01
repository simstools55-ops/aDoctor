# Algorithm Evidence v1

## Purpose

Google検索アルゴリズム更新や検索結果環境の変化を、SIMS Article Doctorが診断へ統合するためのPlatform共通境界を定義する。

## Core rule

**Algorithm information is Evidence, not Diagnosis.**

アップデート期間との時間的一致だけで、順位・クリック・表示変動の原因をGoogleアップデートと断定してはならない。

Doctorは少なくとも利用可能な次のEvidenceを統合して判断する。

- Search Console performance and query evidence
- SERP composition and intent evidence
- Article content quality, factual accuracy, freshness, and alignment
- Site-wide or segment-wide performance evidence
- Treatment and monitoring history
- Officially confirmed Google Search update information

## Source boundary

Google Search updateの存在・名称・rollout期間は、可能な限りGoogle公式情報をPRIMARY/OFFICIAL evidenceとして扱う。第三者の変動観測だけで公式アップデートを確定しない。

## Causation boundary

Algorithm Evidenceは次のような役割評価を取り得る。

- `PRIMARY_FACTOR`
- `CONTRIBUTING_FACTOR`
- `POSSIBLE_FACTOR`
- `UNLIKELY_FACTOR`
- `NOT_SUPPORTED`

ただし、これらは因果関係の数学的証明を意味しない。Evidence不足時は確信度を下げ、断定表現を避ける。

## Treatment boundary

アップデート中または直後で変動が不安定な場合、Doctorは`WAIT`を選択できる。`WAIT`は放置ではなく、観察対象・再診時期・避けるべき変更を伴う経過観察である。

重大な事実誤認、危険情報、検索意図の明確な不一致など、待つことで利用者・読者リスクが増える問題がある場合は、Algorithm Evidenceのみを理由に必要な治療を延期してはならない。

## Product responsibility

- SBM: GSC、記事、履歴、site impact等のEvidenceを収集・集計・保存・配送する。
- Doctor: Algorithm Evidenceを外部環境Evidenceとして評価し、他Evidenceと統合して診断・Treatment Strategyを決定する。
- Writer / Creator / Merge: SBMから発行された紹介状・依頼だけを処置する。Algorithm Evidenceを理由に独自Routingしない。

## Prohibited shortcuts

- 「アップデート期間と重なった = アップデートが原因」
- 「サイトが下落した = 全記事を全面リライト」
- 「アップデート中 = 何も確認せず待つ」
- 非公式情報だけで公式Update名や期間を確定する
