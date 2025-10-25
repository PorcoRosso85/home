# ADR 0.11.7: DoD整合性確認の完了（CUEガバナンス）

- **Status**: Confirmed
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.4（sops-nix / flake細粒度 / manifest guard / Terranix）, ADR 0.11.5（Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針）, ADR 0.11.6（Finalize Secrets/Guard/IaC/Zoning policies）

---

## 0. 結論

- DoD修正後の定義どおり、**「全CUEに何を作るか」の整合性確認を完了**。
- 本ADRは **既存決定（0.11.4〜0.11.6）を確認・固定** する記録であり、新規方針は含まない。
- CUEガバナンスの全体像（policy/cue + provisioning/cue + manifest_schema.cue）が矛盾なく定義された。

---

## 1. 背景

### 1.1 DoD定義の確認

ADR 0.11.4〜0.11.6を通じて以下が確定した：

| CUEディレクトリ | 責務 | 検証対象 | VCS追跡 |
|---------------|------|---------|---------|
| `policy/cue/` | リポジトリ構造・依存ルール・命名規則 | 静的コード構造 | ✅ 全ファイル |
| `infra`（Terranix→OpenTofu 入力のCUEスキーマ群） | OpenTofu出力値の型・契約検証 | 実行時インフラ値 | ✅ スキーマのみ |
| `policy/cue/schemas/manifest_schema.cue` | Manifest Guard型定義 | manifest生成物の型 | ✅ 型のみ |

### 1.2 整合性確認の範囲

本ADRは以下を確認した：

1. **CUE相互独立性**: `policy/cue` と `provisioning/cue` は相互にimportしない
2. **manifest生成と検証の分離**:
   - manifest生成：`nix build .#manifest.<svc>` → `out/manifest/<svc>.cue`（VCS非追跡）
   - manifest型定義：`policy/cue/schemas/manifest_schema.cue`（VCS追跡）
   - manifest検証：allowlist（`interfaces/<svc>/infra.allow.cue`）とのdiff
3. **Format統一**: CUE固定（JSON/YAML不採用）
4. **S3排除・R2固定**: 全ストレージ/バックエンドをR2に統一（S3使用禁止）

---

## 2. 確認済み事項

### 2.1 CUEガバナンス全体図

```
policy/cue/
├─ schemas/
│  ├─ deps.cue                    # 依存ルール検証
│  └─ manifest_schema.cue         # Manifest型定義（VCS追跡）
└─ checks/                        # 構造検証ロジック

infra/provisioning/cue/
├─ schemas/                       # Tofu output型定義
└─ checks.cue                     # 実値検証ロジック

(生成物・非追跡)
out/manifest/<svc>.cue            # flake生成（nix build .#manifest.<svc>）

interfaces/<svc>/infra.allow.cue  # allowlist（VCS追跡）
```

### 2.2 各CUEの責務確認

#### policy/cue/
- **責務**: リポジトリ構造ガバナンス
- **検証内容**:
  - 許可ディレクトリ（`#AllowedInfraDirs`）
  - 依存方向（apps→infra、infra↛apps）
  - 命名規則
- **独立性**: provisioning/cueをimportしない

#### infra（Terranix→OpenTofu 入力のCUEスキーマ群）
- **責務**: IaC出力値検証
- **検証内容**:
  - `tofu output -json` の型チェック
  - R2エンドポイント/バケット名の契約
- **独立性**: policy/cueをimportしない

#### policy/cue/schemas/manifest_schema.cue
- **責務**: Manifest型定義のみ
- **VCS追跡理由**: 型が契約であり、生成物の形状を保証
- **生成物との分離**:
  - `manifest_schema.cue`: 型（VCS追跡）
  - `out/manifest/<svc>.cue`: インスタンス（VCS非追跡、flake生成）

### 2.3 Manifest Guardフロー確認

```
1. サービス開発
   ↓
2. nix build .#manifest.<svc>
   ↓（CUE生成）
3. out/manifest/<svc>.cue
   ↓（将来CI実装）
4. allowlist diff
   ↓
5. P0: warn / P1: gate / P2: fail
```

**確認済み**:
- Format: CUE固定（0.11.4/0.11.5/0.11.6踏襲）
- allowlist位置: `interfaces/<svc>/infra.allow.cue`（0.11.6確定）
- 型定義: `policy/cue/schemas/manifest_schema.cue`（0.11.6確定）

### 2.4 ストレージ方針確認

**R2のみ許可・S3使用禁止**（0.11.3/0.11.6踏襲）:

| 用途 | 使用先 | 禁止 |
|-----|--------|------|
| 本番ストレージ | R2 | S3 |
| Tofu state backend | R2 | S3 |
| Logs/観測SoR | R2 | SaaS |

---

## 3. TODO（未実装・将来作業）

本ADRは既存決定の確認記録のため、以下は実装責務外：

### 3.1 Manifest Guard CI実装
- `nix build .#manifest.<svc>` の自動実行
- CUEパース + allowlist diff
- P0→P1→P2段階導入

### 3.2 policy/cue 検証CI
- リポジトリ構造の自動検証
- 依存方向違反の検出

### 3.3 provisioning/cue 検証CI
- `tofu output -json` → `cue vet` の自動化
- R2エンドポイント契約チェック

### 3.4 manifest_schema.cue 実ファイル作成
- 型定義の実装（別PR）

### 3.5 allowlist実ファイル作成
- 各サービスのallowlist配置（別PR）

---

## 4. Implementation Acceptance Criteria

本ADRの完了条件（確認記録として）：

1. ✅ CUEガバナンス全体図が矛盾なく定義されている
2. ✅ policy/cue と provisioning/cue の独立性が明記されている
3. ✅ manifest_schema.cue と生成manifestの分離が明確化されている
4. ✅ Format統一（CUE固定）が確認されている
5. ✅ S3排除・R2固定が再確認されている
6. ✅ 実装・CI・構成変更を含まない（ドキュメントのみ）

---

## 5. Out of scope

以下は**本PRに含めない**：

- 実装（コード変更）
- CI設定追加・変更
- 新規ディレクトリ追加
- `manifest_schema.cue` の実ファイル作成（TODO 3.4）
- allowlist実ファイル作成（TODO 3.5）

---

## 6. 関連ADR

- **ADR 0.11.3**: リポジトリ構造統一 + IaC統合
- **ADR 0.11.4**: sops-nix / flake細粒度 / manifest guard / Terranix→OpenTofu（R2）
- **ADR 0.11.5**: Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針（TODO宣言）
- **ADR 0.11.6**: 0.11.5のTODO確定（Secrets/Guard/IaC/Zoning policies）

---

## 7. まとめ

本ADRにより、以下が確認された：

1. **CUE責務分離**: policy/cue（構造）/ provisioning/cue（実値）/ manifest_schema.cue（型）が独立
2. **Manifest Guard全体像**: 生成（flake）→ 型（schema）→ 検証（allowlist diff）の流れが確定
3. **Format統一**: CUE固定（JSON/YAML不採用）の再確認
4. **ストレージ方針**: R2のみ・S3禁止の最終確認

**この文書は確認記録であり、実装・CI追加は別PRで実施。**
