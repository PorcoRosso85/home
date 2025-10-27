# ADR 0.11.3: リポジトリ構造統一 + IaC統合（最終形）

- **ID**: adr-0.11.3
- **Date**: 2025-10-24 (JST)
- **Status**: Accepted
- **Supersedes**: adr-0.11.2
- **Scope**: 0.11.2の全内容 + OpenTofu × Nix × CUE による IaC統合

---

## 0. 要約

本ADRは **最終形のリポジトリ構造宣言** であり、以下を包含する：

### 0.11.2から継承（変更なし）
- **命名規則**: `<ドメイン>-<用途>-<形態>` 形式に統一
- **infra/sdk 解体**: `presentation-runtime/` + `content-build-tools/` に分割済み
- **interfaces命名統一**: `docs-build-cli/` + `docs-static-site/`
- **dist配置ルール**: `interfaces/docs-static-site/dist/` のみ（CDN/Pages配信用）

### 0.11.3で追加
- **IaC統合**: `infra/provisioning/` 追加（OpenTofu + Nix + CUE）
- **ストレージ方針**: R2のみ（S3は使用禁止）
- **公式ワークフロー**: tofu output → CUE検証 → .env生成

---

## 1. 背景

### 1.1 0.11.2までの達成内容
- リポジトリ構造の命名統一
- infra/sdkの責務分離
- dist配置ルールの明文化

### 1.2 残された課題
- **インフラプロビジョニングの再現性**: クラウドリソースの作成手順が統一されていない
- **環境変数の検証不足**: .envファイルが手動管理で型安全性がない
- **ツールチェーンの非固定**: Terraform/Tofuのバージョンが環境ごとに異なる可能性

### 1.3 0.11.3での解決
OpenTofu × Nix × CUE による統合で、クラウド環境とローカル環境を同一宣言から確定的に生成可能にする。

---

## 2. 決定内容

### 2.1 IaC統合の7原則

#### 原則1: OpenTofu を標準IaCツールとして採用
- Terraform互換でOSS
- 宣言的な差分管理（Pulumiのような動的生成を避ける）

#### 原則2: Nix でツールチェーンのバージョン固定
- `infra/provisioning/flake.nix` でtofu/cue/sopsのバージョンをピン留め
- `nix develop` で常に同一IaC実行環境を再現

#### 原則3: CUE で Tofu 出力の構造・契約を検証
- `tofu output -json` の結果を `cue/schemas/` で型定義
- `cue vet` で検証し、不正な値を .env に流さない

#### 原則4: State保存方針の2段階ポリシー
- **開発環境**: `infra/provisioning/state/` にローカルstate（.gitignore対象）
- **CI/本番**: R2バックエンドを使用（共有・ロック付き）

#### 原則5: Output検証済みの値のみアプリ側へ供給
公式フロー：
```
1. tofu plan/apply 実行
2. tofu output -json → infra/provisioning/outputs/ へ書き出し
3. cue vet で検証（cue/checks.cue）
4. 検証済みの値を scripts/export-env.sh で .envrc / CIシークレットに変換
```

#### 原則6: Pulumi等の動的IaCは採用しない
- 理由: 静的な差分可視化を重視
- tofu planの結果が誰でも読める宣言的な形式であることを保証

#### 原則7: infra/provisioning/ がIaCの単一真実（SSOT）
- IaC定義が他ディレクトリに散らばることを禁止
- 全クラウドリソースはここで宣言・管理

---

### 2.2 infra/provisioning/ ディレクトリ構成

```
infra/provisioning/
├─ modules/                    # Tofu module定義群（クラウドリソース単位）
│  ├─ storage_bucket/          # R2バケット作成
│  ├─ cdn_distribution/        # CDN配信設定
│  └─ compute_instance/        # コンピュートインスタンス
├─ environments/               # 環境別変数セット
│  ├─ dev/                     # 開発環境設定
│  ├─ staging/                 # ステージング環境設定
│  └─ prod/                    # 本番環境設定
├─ state/                      # 開発ローカルstate置き場（.gitignore）
├─ outputs/                    # tofu output -json の生データ
├─ cue/                        # 出力値のCUEスキーマと検証
│  ├─ schemas/                 # outputスキーマ（型定義）
│  └─ checks.cue               # 検証ロジック
├─ scripts/                    # 公式ラッパスクリプト
│  ├─ plan.sh                  # tofu plan/apply ラッパ
│  ├─ export-env.sh            # 検証済みoutput→.env生成
│  └─ verify.sh                # cue vet / diff検証
├─ flake.nix                   # tofu/cue/sops等のバージョン固定
└─ README.md                   # 運用規約とR2 backendの方針
```

**各要素の責務**:

| ディレクトリ | 責務 |
|-------------|------|
| `modules/` | クラウドリソースの宣言（Tofu module） |
| `environments/` | 環境ごとの変数値（*.tfvars / *.cue） |
| `state/` | 開発時のローカルstate保存（共有しない） |
| `outputs/` | tofu出力の生データ（CUE検証前） |
| `cue/` | 出力値の型定義と検証ロジック |
| `scripts/` | plan/apply/export-envの統一インタフェース |

---

### 2.3 CUEの役割分担（重要）

本リポジトリには2つのCUEディレクトリが存在するが、**完全に独立**している：

| ディレクトリ | 責務 | 検証対象 |
|-------------|------|---------|
| `policy/cue/` | リポジトリ構造・依存ルール・命名規則・層境界 | 静的コード構造 |
| `infra/provisioning/cue/` | OpenTofu出力値の型・契約検証 | 実行時インフラ値 |

**分離の理由**:
- `policy/cue/` はリポジトリの再配置ルールなど構造ガバナンスに集中
- `provisioning/cue/` は本番の実値（R2エンドポイント、バケット名など）を検証
- **相互独立**: `provisioning/cue` は `policy/cue` をimportしない

---

### 2.4 provisioning vs adapters の境界

| 層 | 責務 | 使用ツール |
|----|------|-----------|
| `infra/provisioning/` | クラウドリソースを**作る** | OpenTofu |
| `infra/adapters/` | 作成済みリソースに**つなぐ** | SDK/クライアント |

**データの流れ**:
```
provisioning → (tofu output / .env) → adapters
```

**ガード**:
- ✅ `adapters/` はクラウドリソースを作成しない（接続のみ）
- ✅ `provisioning/` はアプリに直接依存しない（.env経由のみ）

---

### 2.5 ストレージ方針の最終決定

#### R2のみ許可・S3使用禁止

ADR 0.11.1で決定したストレージ方針を再確認・強化：

| 用途 | 使用先 | 禁止 |
|-----|--------|------|
| 本番ストレージ | R2 | S3 |
| CI/開発 | MinIO (R2互換) | S3 |
| Tofu state backend | R2 | S3 |

**理由**:
- S3は将来的な復活も許可しない
- R2が唯一のクラウドストレージ/バックエンド
- MinIOはローカル/CI専用（R2互換として）

**tree.md およびコード内での明記**:
```
infra/adapters/storage/
├─ r2/                     # 本番ストレージ
├─ drive/                  # 代替（必要に応じて）
└─ (s3/)                   # 廃止済み・復活禁止
```

---

## 3. 0.11.2内容の継承（再掲）

以下は **0.11.2で導入済み** であり、**0.11.3では変更していない**：

### 3.1 命名規則
**原則**: `<ドメイン>-<用途>-<形態>`

| 旧名 | 新名（0.11.2で確定） |
|-----|---------------------|
| `cli-docs` | `docs-build-cli` |
| `web-docs-vanilla` | `docs-static-site` |

### 3.2 infra/sdk 解体
```
0.11.1以前: infra/sdk/ui-wc/x-deck/, infra/sdk/md-tools/
0.11.2以降: infra/presentation-runtime/x-deck/
           infra/content-build-tools/shared|md2html|mmd2svg|pdf-export/
```

### 3.3 dist配置ルール
- ✅ `interfaces/docs-static-site/dist/` のみ正当（CDN/Pages配信用）
- ❌ `infra/` 配下は `dist/` を持たない

### 3.4 policy/cue 許可リスト
```cue
#AllowedInfraDirs: [
    "runtimes",
    "adapters",
    "presentation-runtime",    // 0.11.2で追加
    "content-build-tools",     // 0.11.2で追加
    "provisioning",            // 0.11.3で追加
]
```

---

## 4. 他レイヤーとの関係

| 層 | infra/provisioning/ との関係 |
|----|----------------------------|
| `contracts/` | 参照しない（純粋スキーマ定義） |
| `domains/` | 参照しない（純粋ドメインロジック） |
| `apps/` | tofu output から得られる .env を通じて依存先URLやBucket名を参照 |
| `interfaces/` | .env 経由で値を参照可能（直接tofuを叩かない） |
| `policy/cue/` | 逆依存を禁止（provisioning から上層をimportしない） |

---

## 5. 公式ワークフロー

### 5.1 開発環境での実行

```bash
cd infra/provisioning/

# Nix環境に入る
nix develop

# Plan実行（ローカルstate使用）
./scripts/plan.sh dev

# Apply実行
./scripts/apply.sh dev

# Output検証 + .env生成
./scripts/export-env.sh dev
# → 検証済みの値が .envrc に書き出される
```

### 5.2 CI/本番での実行

```yaml
# ci/workflows/infra-deploy.yml
- name: Setup Nix
  uses: cachix/install-nix-action@v22

- name: Configure R2 backend
  run: |
    export TF_STATE_BACKEND=r2
    export R2_BUCKET=terraform-state-prod

- name: Plan infrastructure
  run: nix develop -c ./scripts/plan.sh prod

- name: Apply infrastructure
  run: nix develop -c ./scripts/apply.sh prod

- name: Verify outputs
  run: nix develop -c ./scripts/verify.sh prod

- name: Export to secrets
  run: nix develop -c ./scripts/export-env.sh prod
```

---

## 6. セキュリティポリシー

### 6.1 検証前の値はアプリに渡さない

`tofu output -json` の生データを直接 .env に書き込むことを**禁止**。

**必須フロー**:
```
tofu output -json → outputs/ → cue vet → (OK) → export-env.sh → .env
                                      ↘ (NG) → エラー停止
```

### 6.2 State暗号化

- CI/本番のR2バックエンドは暗号化・ロック有効化必須
- `sops` / `age` を使用（Nix flakeで固定）

### 6.3 Secrets管理

- `.env` ファイルは `.gitignore` 対象
- CIシークレットへの書き込みは `export-env.sh` 経由のみ

---

## 7. 再配置ルール（0.11.2継承）

### 許可される操作
- ✅ `git mv`（ディレクトリ/ファイル移動）
- ✅ importパス置換
- ✅ flake出力名の整合
- ✅ policy/cue 更新（新ディレクトリ名の追加）

### 禁止される操作
- ❌ 関数/クラスシグネチャ変更
- ❌ 新規機能追加（provisioning/の追加は構造追加として許可）
- ❌ `contracts/ssot/**` 変更
- ❌ 依存の追加更新

---

## 8. CI必須条件（不変）

1. ✅ 全テスト緑（ユニット/統合/契約/E2E）
2. ✅ `nix flake check` 緑
3. ✅ `policy/cue` 違反0
4. ✅ `contracts/ssot/**` 差分0

---

## 9. 完了条件（DoD）

### 0.11.2継承部分
1. `infra/sdk/` が削除され、2つのディレクトリに分割されている
2. `interfaces/` の命名が `docs-*` 形式に統一されている
3. dist配置ルールがドキュメント化されている

### 0.11.3追加部分
4. `infra/provisioning/` が追加され、7原則が実装されている
5. `policy/cue` と `provisioning/cue` の役割分担が明文化されている
6. R2のみ許可・S3禁止がコメントとADRに明記されている
7. 公式ワークフロー（tofu → cue → export-env）が実装されている
8. CI全緑を維持

---

## 10. 関連ADR

- **ADR 0.10.8**: SSOT-first & thin manifest
- **ADR 0.10.10**: Flake-driven manifest
- **ADR 0.10.11**: consumes/Secrets/SBOM/CVE
- **ADR 0.10.12**: Orchestration v4.1b（Superseded）
- **ADR 0.11.0**: 4層構成への統一（Superseded）
- **ADR 0.11.1**: ストレージ方針明確化（Superseded）
- **ADR 0.11.2**: 命名統一・sdk解体・dist責務固定（Superseded by 0.11.3）
- **ADR 0.11.3**: 本ADR（最終形：0.11.2 + IaC統合）

---

## 11. まとめ

本ADRにより、以下が確定した：

1. **リポジトリ構造**: 命名・分割・dist配置が統一された（0.11.2継承）
2. **IaC統合**: OpenTofu × Nix × CUE で再現可能なインフラ管理
3. **ストレージ方針**: R2のみ・S3使用禁止の最終決定
4. **検証フロー**: tofu output → CUE検証 → .env生成の公式化
5. **責務分離**: provisioning（作る）/ adapters（つなぐ）の明確化

**この文書が現行の正（SSOT）であり、過去のADRは履歴用として参照のみ。**
