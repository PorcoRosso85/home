# ADR 0.11.1: 4層＋SSOTの再配置（微修正）/ 既定ストレージ＝R2 / CI＝MinIO / 0.11.0を置換

- **ID**: adr-0.11.1
- **Date**: 2025-10-23 (JST)
- **Status**: Superseded
- **Superseded by**: adr-0.11.2
- **Supersedes**: adr-0.11.0
- **Scope**: 構成・命名・依存宣言の明確化とストレージ方針（※機能/契約/コードは非変更）

> **Note**: この ADR は adr-0.11.2 により Superseded されました。命名統一・infra/sdk解体・dist責務固定により更新。履歴参照用に保持。

---

## 0. 要約

- 4層構成（`interfaces → apps → domains → contracts`、依存宣言は **apps→infra**）を再確認
- **既定ストレージは R2**。**CI は MinIO**（ローカル互換）を使用
- **AWS S3 は使わない**（言及も削除）。必要なら将来の別ADRで再検討

---

## 1. 背景（0.11.0との差分）

- 0.11.0では R2/MinIO に加え S3にも触れていたが、運用方針を **R2+MinIO に限定**
- 影響は **ドキュメントのみ**（構成・契約・コードの振る舞いは非変更）

---

## 2. 決定

### ストレージ方針
- **本番**: **R2**（Cloudflare R2）
- **CI/開発**: **MinIO**（R2互換エンドポイントで動作）
- **AWS S3**: 使用しない（記述も削除）

### DI集約
- `interfaces/*/wire.*` で Adapter注入を一元化

### 命名規則
- **kebab-case**統一
- **出力名 = パス名**（flakeで検査）

### 依存宣言
- `infra/` 配下に一元化
  - `runtimes/*/constraints.txt`
  - `adapters/*/*/requirements.in`

---

## 3. 再配置ルール（再掲）

### 許可される操作
- ✅ `git mv`（ディレクトリ/ファイル移動）
- ✅ importパス置換
- ✅ flake出力名の整合
- ✅ `wire` のDI差し替え

### 禁止される操作
- ❌ 関数/クラスシグネチャ変更
- ❌ 新規機能追加
- ❌ `contracts/ssot/**` 変更
- ❌ 依存の追加更新

---

## 4. CI必須条件（不変）

1. ✅ 全テスト緑（ユニット/統合/契約/E2E）
2. ✅ `nix flake check` 緑
3. ✅ `policy/cue` 違反0
4. ✅ `contracts/ssot/**` 差分0

---

## 5. ストレージENV設定例

> 変数名は中立表記。既存のAWS系名を使っている場合は **ENVエイリアス**で吸収可。

### 開発/CI（MinIO）
```env
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_REGION=auto
STORAGE_FORCE_PATH_STYLE=true
STORAGE_ACCESS_KEY=minio
STORAGE_SECRET_KEY=minio123
STORAGE_BUCKET=app-blobs
STORAGE_PREFIX=dev/
```

### 本番（R2）
```env
STORAGE_ENDPOINT=https://<account>.r2.cloudflarestorage.com
STORAGE_REGION=auto
STORAGE_FORCE_PATH_STYLE=false
STORAGE_ACCESS_KEY=<r2-access-key>
STORAGE_SECRET_KEY=<r2-secret-key>
STORAGE_BUCKET=app-blobs-prod
STORAGE_PREFIX=prod/
```

---

## 6. 記述上の変更（0.11.0 → 0.11.1）

| 項目 | 0.11.0 | 0.11.1 |
|-----|--------|--------|
| storage adapters | R2 / S3 / Drive | R2 / Drive |
| 既定実装 | 明記なし | R2 |
| CI環境 | 明記なし | MinIO（R2互換） |

`infra/adapters/storage/` から `s3/` の記載を削除（R2を既定に一本化）

---

## 7. 完了条件（DoD）

1. ドキュメントが本ADRと一致（tree含む）
2. CI全緑を維持
3. S3への言及が全て削除されている

---

## 8. 関連ADR

- **ADR 0.10.8**: SSOT-first & thin manifest
- **ADR 0.10.10**: Flake-driven manifest
- **ADR 0.10.11**: consumes/Secrets/SBOM/CVE
- **ADR 0.10.12**: Orchestration v4.1b（Superseded by 0.11.0）
- **ADR 0.11.0**: 4層構成への統一（Superseded by 0.11.1）
- **ADR 0.11.1**: 本ADR（ストレージ方針明確化）
