# SIMS Machine Output Policy v1

## Preserve machine data
AI・製品間通信では以下を保持する。
- Contract / Version
- Evidence / Evidence Confidence
- Treatment Strategy
- allowed_scope / blocked_scope
- actions_permitted / actions_prohibited
- Routing / Case correlation
- Internal validation results

Presentationの簡素化を理由にMachine情報を削除してはならない。

## Adapter responsibility
Machine Contractのフィールドが製品間で異なる場合、Adapterが明示的に正規化する。
利用者向けPresentationで補完することでContract不整合を隠してはならない。

## Doctor to SBM to specialist
Doctorの結果はSBMへ返す。SBMは専門家向け依頼へ正規化し、Writer / Creator / Mergeへ渡す。
専門家はMachine情報を守りつつHuman OutputをPresentation Standardに従って生成する。
