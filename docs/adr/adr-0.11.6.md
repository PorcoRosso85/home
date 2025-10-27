# ADR 0.11.6: Finalize Secrets/Guard/IaC/Zoning policies

- **Status**: Proposed
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.4（sops-nix / flake細粒度 / manifest guard / Terranix）, ADR 0.11.5（Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針）
- **Finalizes**: ADR 0.11.5 の TODO 3.1, 3.3, 3.4, 3.5, 3.6

---

## 0. 決定（確定事項）

本ADRは、ADR 0.11.5で未確定だった運用方針を確定する。

### 0.1 Secrets運用
- **ホスト起源のage鍵**: 初回起動で生成。中央配布なし。
- **暗号化フロー**: 平文は初期入力時のみ一時保有 → 即座に sops-nix で暗号化。
- **復号**: activation時に実施。外部金庫・R2バックアップは不採用（0.11.5踏襲）。
- **復旧経路**: ホスト鍵 + CI Secrets側のバックアップ鍵で二経路確保。

### 0.2 Flakes/leaf規約
- **命名例**: `infra.<domain>.<component>.<leaf>`（層・役割が名前で判別可能）
- **依存方向**: apps→infra の一方向のみ。infra→apps 禁止。
- **横依存禁止**: サービスは必要leafのみを束ねる（他サービスのleaf参照禁止）。

### 0.3 Manifest Guard仕様
- **Format**: CUE固定。生成物（インスタンス）はVCS非追跡（0.11.4/0.11.5踏襲）。
- **型定義**: `policy/cue/schemas/manifest_schema.cue` として型のみVCS管理（混同回避のため `manifest.cue` から改名）。
- **allowlist位置**: `interfaces/<svc>/infra.allow.cue`
- **比較規則**:
  - subset一致（allowlist ⊇ 実使用infraセット）
  - 禁止キー検出（例: `infra.experimental.*` の本番混入）
- **段階導入**:
  - P0: warn（ログ出力のみ）
  - P1: gate（手動承認が必要）
  - P2: fail（CI失敗）

### 0.4 観測（Logs/分析）
- **R2 = 唯一の長期SoR**: SaaS不使用（コスト・ロックイン回避）。
- **Loki等**: 任意の可視化レイヤ（必須ではない）。
- **重解析**: R2 → ETL（例: Parquet変換） → クエリ（例: Trino）。

### 0.5 IaC細部
- **R2バケット/キー命名例**: `infra-state/<env>/<svc>.tfstate`
- **provider pin例**: `>=1.8,<2.0`（major version固定）
- **ロック**: 当面CI直列実行。将来R2オブジェクトロック（S3互換）導入を検討。

### 0.6 ゾーニング
- **P0/P1**: zoneラベルをCUE/flakeメタで宣言管理（物理移動しない）。
- **P2**: stable昇格後のみ物理移動。互換期間はエイリアス/再エクスポート許可。
- **stable昇格条件例**:
  - 2環境稼働（staging + production）
  - アラート整備完了
  - 半年無事故運用

---

## 1. 背景

ADR 0.11.5で以下が未確定として残されていた：
- TODO 3.1: Secrets細部
- TODO 3.3: Manifest Guard細部
- TODO 3.4: 観測バックエンド
- TODO 3.5: IaC細部
- TODO 3.6: ゾーニング

これらを本ADRで確定し、運用可能な状態にする。

---

## 2. 詳細

### 2.1 Secrets運用の詳細化

**age鍵の生成と管理**:
```bash
# 初回起動時（自動）
age-keygen -o /etc/age/host.key
chmod 600 /etc/age/host.key
```

**暗号化フロー**:
1. 平文をCLI/UIから入力
2. 即座に `sops-nix` で暗号化（`.sops.yaml` に従う）
3. 平文を破棄（メモリクリア）
4. 暗号化ファイルのみVCS追跡

**復旧経路**:
- **経路1**: ホスト鍵（`/etc/age/host.key`）で復号
- **経路2**: CI Secrets側のバックアップ鍵で復号（ホスト喪失時）

**外部金庫を採用しない理由**:
- シンプル運用優先（age + sops-nix で完結）
- ローテーション・監査は手動管理で開始、後で自動化検討

---

### 2.2 Flakes/leaf規約の明確化

**命名規則**:
```
infra.<domain>.<component>.<leaf>

例:
  infra.video.encoder.ffmpeg
  infra.search.index.kuzu
  infra.storage.r2
```

**依存グラフ例**:
```
apps/video/
  ↓ (使用)
infra.video.encoder.ffmpeg
infra.storage.r2

✅ OK: apps → infra
❌ NG: infra → apps
❌ NG: apps/video → apps/search
```

---

### 2.3 Manifest Guard仕様の確定

**型定義の配置**:
```
policy/cue/schemas/manifest_schema.cue  # 型のみVCS（旧 manifest.cue から改名）

例:
#ManifestSchema: {
  service: string
  infra_deps: [...string]
  forbidden: [...string]
}
```

**allowlist例**:
```cue
// interfaces/video/infra.allow.cue
package video

allowed_infra: [
  "infra.video.encoder.ffmpeg",
  "infra.storage.r2",
]

forbidden_patterns: [
  "infra.experimental.*",
]
```

**比較ロジック（将来CI実装）**:
```
1. nix build .#manifest.video → out/manifest/video.cue
2. CUEパース
3. allowed_infra ⊇ video.cue.infra_deps をチェック
4. forbidden_patterns マッチでfail
5. P0: warn / P1: gate / P2: fail
```

---

### 2.4 観測アーキテクチャの確定

**R2中心のアーキテクチャ**:
```
App/Service
  ↓ (logs/metrics)
OTel Collector
  ↓ (JSONL)
R2 (長期保管・SoR)
  ↓ (ETL)
Parquet/Iceberg
  ↓ (query)
Trino/DuckDB

（任意）
R2 → Loki → Grafana（可視化レイヤ）
```

**SaaS不使用の理由**:
- コスト管理（R2の低コスト性）
- ベンダーロックイン回避
- 全データをR2に集約（SoR統一）

---

### 2.5 IaC細部の確定

**R2 state backend設定例**:
```hcl
terraform {
  backend "s3" {
    bucket = "infra-state"
    key    = "prod/video.tfstate"
    region = "auto"  # R2はregion不要だが互換性のため設定
    endpoints = {
      s3 = "https://<account-id>.r2.cloudflarestorage.com"
    }
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_metadata_api_check     = true
  }
}
```

**provider pin例**:
```hcl
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">=4.0,<5.0"
    }
  }
}
```

**ロック方針**:
- **P0**: CI直列実行（ジョブ排他制御）
- **P1**: R2オブジェクトロック導入検討

---

### 2.6 ゾーニング方針の確定

**P0/P1フェーズ（ラベル管理）**:
```cue
// infra/video/encoder/ffmpeg/flake.nix に対応するメタ
{
  zone: "stable"  // or "experimental"
}
```

**P2フェーズ（物理移動）**:
```
移動前:
  infra/video/encoder/ffmpeg/  (zone=experimental)

昇格後:
  infra/stable/video/encoder/ffmpeg/  (物理移動)
  infra/video/encoder/ffmpeg/         (エイリアス・3ヶ月後削除)
```

**stable昇格条件**:
1. staging + production 2環境で稼働
2. アラート整備完了（SLO/SLI定義済み）
3. 半年無事故運用（Critical障害なし）

---

## 3. 影響

### 3.1 Secrets管理
- ホスト鍵管理の徹底（初回起動スクリプトに組み込み）
- 二経路復旧体制の確保

### 3.2 Manifest Guard
- `manifest_schema.cue` を policy/cue/schemas/ に追加（型のみ）
- allowlist を interfaces/<svc>/ に配置
- CI実装は別PR

### 3.3 観測
- R2中心アーキテクチャへの統一
- Loki等はオプション扱い

### 3.4 IaC
- R2 backend設定の標準化
- provider pin方針の明確化

### 3.5 ゾーニング
- ラベル管理の開始（P0）
- 物理移動は将来フェーズ（P2）

---

## 4. DoD（本PRの完了条件）

1. ✅ 0.11.5のTODO（3.1, 3.3, 3.4, 3.5, 3.6）が確定
2. ✅ 用語統一（sops-nix / Terranix / OpenTofu / R2 / manifest / allowlist / leaf）
3. ✅ 0.11.4/0.11.5と矛盾なし（R2 Secretsバックアップ不採用を踏襲、manifest=CUE固定）
4. ✅ 実装・CI・構成変更を含まない（ドキュメントのみ）

---

## 5. Out of scope

以下は**本PRに含めない**：
- 実装（コード変更）
- CI設定追加・変更
- 新規ディレクトリ追加
- `manifest_schema.cue` の実ファイル作成（別PRで追加）
- allowlist実ファイル作成（別PRで追加）

---

## 6. 関連ADR

- **ADR 0.11.3**: リポジトリ構造統一 + IaC統合
- **ADR 0.11.4**: sops-nix / flake細粒度 / manifest guard / Terranix→OpenTofu（R2）
- **ADR 0.11.5**: Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針（TODO宣言）
- **ADR 0.11.6**: 本ADR（0.11.5のTODO確定）
