# ADR 0.11.2: 命名統一 / infra/sdk解体 / dist責務の固定

- **ID**: adr-0.11.2
- **Date**: 2025-10-23 (JST)
- **Status**: Superseded
- **Superseded by**: adr-0.11.3
- **Supersedes**: adr-0.11.1
- **Scope**: 命名規則の統一・infra/sdk分割・dist配置ルール（※機能/契約/コードは非変更）

> **Note**: この ADR は adr-0.11.3 により Superseded されました。0.11.3は本ADRの全内容 + IaC統合を含む最終形です。

---

## 0. 要約

- **命名規則**: `<ドメイン>-<用途>-<形態>` 形式に統一（例: `docs-build-cli`, `docs-static-site`）
- **infra/sdk 解体**: 責務ごとに分割
  - `infra/presentation-runtime/` （Web Componentランタイム）
  - `infra/content-build-tools/` （MD→HTML等のビルドツール）
- **dist責務の固定**: `interfaces/docs-static-site/dist/` のみ（CDN/Pages配信用）
- **影響範囲**: ドキュメント・ディレクトリ名・policy/cue のみ（実装/契約は非変更）

---

## 1. 背景（0.11.1との差分）

### 問題点
- `infra/sdk/` が曖昧（「何のSDKか」が不明）
- `interfaces/cli-docs/`, `web-docs-vanilla/` の命名が不統一
- `dist/` の配置ルールが暗黙的

### 0.11.2での改善
- 命名から責務を読み取れるようにする
- SRP（単一責務の原則）に沿ってディレクトリを分割
- dist配置ルールを明文化

---

## 2. 決定

### 2.1 命名規則

**原則**: `<ドメイン>-<用途>-<形態>`

| 旧名 | 新名 | 理由 |
|-----|------|------|
| `cli-docs` | `docs-build-cli` | ドメイン（docs）を先頭に |
| `web-docs-vanilla` | `docs-static-site` | 実装詳細（vanilla）を除外 |

### 2.2 infra/sdk 解体

**旧構造**:
```
infra/sdk/
├─ ui-wc/x-deck/       # Web Component
└─ md-tools/           # MD変換ツール群
```

**新構造**:
```
infra/presentation-runtime/
└─ x-deck/             # プレゼンテーション表示ランタイム

infra/content-build-tools/
├─ shared/             # 共通ロジック（out-path, frontmatter等）
├─ md2html/            # MD → HTML変換
├─ mmd2svg/            # Mermaid → SVG
└─ pdf-export/         # HTML → PDF
```

**分割理由**:
- **presentation-runtime**: ブラウザで動く表示制御（ランタイム資産）
- **content-build-tools**: ビルド時に動く変換ツール（ビルドツール）
- 責務が異なるため分離（SRP）

### 2.3 共通ロジックの抽出

`infra/content-build-tools/shared/` を新設：
- `out-path.mjs`: 出力パス計算
- `frontmatter.mjs`: frontmatter解析
- `metadata.mjs`: メタデータ抽出

**目的**: DRY（重複排除）、各ツール間で共有

### 2.4 dist責務の固定

**原則**: distは `interfaces/` の静的配信interface **のみ**が持つ

```
interfaces/docs-static-site/dist/   ✅ OK（CDN/Pages配信用）
infra/content-build-tools/dist/     ❌ NG（infraは配信元ではない）
```

### 2.5 policy/cue 更新

`policy/cue/schemas/deps.cue` に許可追加：
```cue
#AllowedInfraDirs: [
    "runtimes",
    "adapters",
    "presentation-runtime",    // 新規追加
    "content-build-tools",     // 新規追加
]
```

---

## 3. 再配置マッピング

| 旧パス（0.11.1想定） | 新パス（0.11.2） | 操作 |
|---------------------|-----------------|------|
| `infra/sdk/ui-wc/x-deck/` | `infra/presentation-runtime/x-deck/` | `git mv` |
| `infra/sdk/md-tools/md2html/` | `infra/content-build-tools/md2html/` | `git mv` |
| `infra/sdk/md-tools/mmd2svg/` | `infra/content-build-tools/mmd2svg/` | `git mv` |
| `infra/sdk/md-tools/pdf-export/` | `infra/content-build-tools/pdf-export/` | `git mv` |
| （新規） | `infra/content-build-tools/shared/` | 新規作成 |
| `interfaces/cli-docs/` | `interfaces/docs-build-cli/` | `git mv` |
| `interfaces/web-docs-vanilla/` | `interfaces/docs-static-site/` | `git mv` |

---

## 4. 再配置ルール（再掲）

### 許可される操作
- ✅ `git mv`（ディレクトリ/ファイル移動）
- ✅ importパス置換
- ✅ flake出力名の整合
- ✅ policy/cue 更新（新ディレクトリ名の追加）

### 禁止される操作
- ❌ 関数/クラスシグネチャ変更
- ❌ 新規機能追加（shared/ の共通ロジック抽出は例外）
- ❌ `contracts/ssot/**` 変更
- ❌ 依存の追加更新

---

## 5. CI必須条件（不変）

1. ✅ 全テスト緑（ユニット/統合/契約/E2E）
2. ✅ `nix flake check` 緑
3. ✅ `policy/cue` 違反0
4. ✅ `contracts/ssot/**` 差分0

---

## 6. dist配置ルール（明文化）

### 原則
- **interfaces/** の静的配信interface **のみ**が `dist/` を持つ
- **infra/** は `dist/` を持たない（配信元ではない）

### 実装
```
interfaces/docs-static-site/
├─ flake.nix
├─ src/index.html
├─ public/
└─ dist/                    # ✅ CDN/Pages配信用（.gitignore対象）
   ├─ index.html
   ├─ sections/
   └─ assets/
```

### CI/CD
```yaml
# ci/workflows/docs-build.yml
- name: Build docs
  run: nix run .#docs-build-cli -- build

- name: Deploy to Pages
  uses: cloudflare/pages-action@v1
  with:
    directory: interfaces/docs-static-site/dist
```

---

## 7. 完了条件（DoD）

1. `infra/sdk/` が削除され、2つのディレクトリに分割されている
2. `interfaces/` の命名が `docs-*` 形式に統一されている
3. `policy/cue/schemas/deps.cue` が更新されている
4. dist配置ルールがドキュメント化されている
5. CI全緑を維持

---

## 8. 関連ADR

- **ADR 0.10.8**: SSOT-first & thin manifest
- **ADR 0.10.10**: Flake-driven manifest
- **ADR 0.10.11**: consumes/Secrets/SBOM/CVE
- **ADR 0.10.12**: Orchestration v4.1b（Superseded）
- **ADR 0.11.0**: 4層構成への統一（Superseded）
- **ADR 0.11.1**: ストレージ方針明確化（Superseded by 0.11.2）
- **ADR 0.11.2**: 本ADR（命名統一・sdk解体・dist責務固定）
