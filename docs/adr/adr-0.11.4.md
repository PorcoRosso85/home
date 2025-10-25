# ADR 0.11.4: sops-nix / fine-grained flakes / manifest guard / Terranix→OpenTofu（R2）

- **Status**: Accepted
- **Date**: 2025-10-24 (JST)
- **Relates**: ADR 0.11.2（命名統一・sdk解体・dist責務固定）, ADR 0.11.3（IaC統合）

## 0. 決定（要約）
1) **Secrets**: sops-nixで暗号化管理。平文はリポ/ストアに残さない。復号はactivation時に実施。
2) **Flakes細粒度**: infraは**leaf出力**へ分割。各サービスは必要leafのみを束ねてビルド。
3) **Manifest Guard**: 各サービスの実使用infraを**flake出力（manifest）で生成**し、サービス側の**allowlist**と比較検証（将来CIで逸脱をfail）。
4) **IaC**: TerranixでOpenTofu入力を生成。**remote stateはR2(S3互換)**を用い、**prod/stg/dev**で分離・ロック運用を前提化。

> 実装・CI導入は別PR。今回は方針の確定とドキュメント反映のみ。

## 1. 背景
- 複数サービスを同一リポで運用しつつ、**1 VPS = 1 サービス**への分離容易性を保持したい。
- infra肥大を防ぎ、必要部品だけを持ち出してデプロイできる構造にする必要がある。

## 2. 詳細
### 2.1 Secrets（sops-nix）
- 機密は`.sops.*`等で暗号化。復号はNixOS activationで行い、env/systemdへ注入。
- 平文コミットは禁止（将来CIで検出）。

### 2.2 Flakesの細粒度化
- `infra/*`は**leafパッケージ**として独立ビルド可能に設計（実装は別PR）。
- サービス出力は、参照するleafのみを束ねる（最小依存での配布・分離を容易化）。

### 2.3 Manifest Guard
- 各サービスの「実使用infraセット」を**flake出力（CUE。flake.nixが生成）**として生成。例：`out/manifest/<svc>.cue`（VCS非追跡）。
- サービス側の**allowlist**（例: `interfaces/*/infra.allow.cue`）と**機械比較**し、逸脱を検出（将来CIでfail）。
- これにより"勝手な横依存"や"本番混入"を抑止。
- **Format**: CUE（JSONは採用しない）。将来のCI実装では `nix build .#manifest.<svc>` → CUEパース → allowlistとdiff で固定化予定。

### 2.4 IaC（Terranix→OpenTofu + R2 remote state）
- Terranixで環境別（prod/stg/dev）のOpenTofu入力を生成。
- **remote stateはR2**を利用し、ロック・バージョン・環境分離を前提化。
- State/秘密はHCLに直書きしない（変数/Secrets連携で扱う）。

## 3. 例（非拘束・実装は別PR）
- Manifest生成イメージ：
```
nix build .#manifest.docs
```
生成物: `out/manifest/docs.cue`（例）

- R2 backendの概念（S3互換を想定）：
```hcl
terraform { backend "s3" {} }  // 実endpoint/bucket/keyは別管理
```

- sops-nix運用の原則：
  - 平文コミット禁止
  - 復号はactivation時、シークレットはenv/systemdへ

## 4. 影響
- リポは単一のまま、最小部品だけをデプロイ可能に。
- infra肥大の結合度を下げ、将来の1 VPS = 1 サービス分離を簡易化。

## 5. DoD（今回）
- 本ADRとtree.mdに方針が反映され、用語が一致している。
- 実装・CIは次PRで追加することを明記。

## 6. Out of scope / TODO
- **監視バックエンド選定（Loki/Tempo/Mimir等）**は次回議論（OTel Collector導入方針は維持）。
- infra/stable / infra/experimental のゾーニングは再議論。
