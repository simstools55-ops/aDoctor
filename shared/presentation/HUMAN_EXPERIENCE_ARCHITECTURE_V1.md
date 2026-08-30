# SIMS Human Experience Architecture v1

## Purpose
SIMS Editorial Platformは、機械が判断するための情報と、利用者が作業するための情報を分離する。

## Three layers
1. Machine Layer: Contract、Evidence、Confidence、Routing、Scope、Internal Flags、JSONを保持する。
2. Presentation Layer: Machine Layerの情報から利用者に必要な内容だけを選択・整形する。
3. Human Layer: 利用者が迷わず作業できる完成形を提示する。

## Platform scope
本ArchitectureはSBM、Doctor、Writer、Creator、Mergeおよび各Claude実装の共通方針である。

## Adoption policy
- RC3先行適用: Doctor / SBM / Writer
- Specification-only adoption: Creator / Merge
- Creator / Mergeは後続フェーズでPresentation実装を追加する。今回のShared更新だけを理由に既存出力を壊してはならない。

## Core rule
機械向け情報をそのままHuman Layerへ露出してはならない。Human Layerは「利用者が次の操作を実行できること」を最優先する。
