# ADR 0.11.0: リポ構成・Flake・依存宣言規約（4層＋SSOT）

- **ID**: adr-0.11.0
- **Date**: 2025-10-23 (JST)
- **Status**: Superseded
- **Superseded by**: adr-0.11.1
- **Supersedes**: adr-0.10.12
- **Scope**: リポジトリ全体の層構成・依存管理・命名規約

> **Note**: この ADR は adr-0.11.1 により Superseded されました。ストレージ方針の明確化（R2+MinIO、S3削除）により更新。履歴参照用に保持。

---

## 0. 要約

- **目的**: 迷いゼロの配置・依存一元化・置換容易性・CIで機械ガード
- **4層構造**: `interfaces → apps → domains → contracts` + `apps → infra`
- **依存宣言**: `infra/` のみ（`runtimes/` と `adapters/`）。他層は宣言禁止
- **不変条件**: API/DB/イベント契約・振る舞い・依存バージョンは変更不可
- **移行方針**: 再配置のみ。git mv + importパス置換 + flake出力名整合のみ許可

---

## 1. 背景

### 課題
- `deployables/` と `features/` の階層不統一
- 依存宣言が各所に分散（追跡困難）
- ドメインロジックと外部FWの結合
- 構成変更時のデグレリスク

### ADR 0.10.12からの変更
- **orchestration実装の再配置**: `features/opencode-autopilot/` → `infra/adapters/opencode/autopilot/`（Port実装として）
- **Gateway/Workerの再配置**: `deployables/opencode-{gateway,worker}/` → `interfaces/http-*` + `apps/*/workflows/`
- **依存宣言の統一**: 全ての外部依存を `infra/runtimes/` と `infra/adapters/` に集約

---

## 2. 決定事項

### 層構成（4層 + インフラ）

```
interfaces → apps → domains → contracts
              ↓
           infra
```

#### 各層の責務

| 層 | 責務 | 依存先 | 禁止事項 |
|---|------|--------|---------|
| **interfaces/** | 入口（HTTP/gRPC/CLI/Web）、wire.pyでDI | apps + infra.runtimes | ビジネスロジック記述 |
| **apps/** | ユースケース/編成、型変換 | domains + infra.adapters | 外部I/O直接呼出 |
| **domains/** | 純粋ロジック、Port定義 | contracts | 外部FW/SDK import |
| **contracts/** | DDL/IDL/イベント定義（SSOT） | なし | 実装コード |
| **infra/** | ランタイム/SDK/Adapter実装 | なし（leaf） | ビジネスロジック |

### 依存宣言の一元化

**原則**: 依存宣言は `infra/` 配下のみ許可

```
infra/
├─ runtimes/<name>/
│  ├─ flake.nix          # ランタイム束（FW/ツール）
│  └─ constraints.txt    # pip系制約
└─ adapters/<port>/<impl>/
   ├─ flake.nix          # Adapter実装
   └─ requirements.in    # 依存宣言
```

### 命名規約

- **ディレクトリ/ファイル**: kebab-case統一
- **Flake出力**: `出力名 = パス名`（ズレはCI fail）
  - `domains/<bc>` → `packages.<sys>.domain.<bc>`
  - `apps/<app>` → `apps.<sys>.<app>` （type="app"）
  - `interfaces/<proto>-<app>` → `apps.<sys>.interface.<proto>-<app>`
  - `infra/runtimes/<name>` → `packages.<sys>.runtimes.<name>`
  - `infra/adapters/<port>/<impl>` → `packages.<sys>.adapters.<port>-<impl>`

### Flake運用

- **ルート単一flake.lock**: 全sub-flakeは `inputs.nixpkgs.follows = "nixpkgs"`
- **devShells集約**: `infra/flake.nix` で ruff/pytest/deadnix/statix を提供
- **domains/のdevShell禁止**: 外部非接続を保証

---

## 3. 再配置ルール

### 許可される操作
- ✅ `git mv`（ディレクトリ/ファイル移動）
- ✅ importパス置換（移動に伴うパス修正）
- ✅ flake出力名の整合（出力名=パス名）
- ✅ `wire.py` のDI差し替え（Port→Adapter注入）

### 禁止される操作
- ❌ 関数/クラスシグネチャ変更
- ❌ 新規機能追加
- ❌ `contracts/ssot/**` の変更（schema.sql/events.cue/openapi.yaml/proto）
- ❌ 依存追加/更新（constraints.txt/requirements.in）

### CI必須条件
1. 全テスト不変緑（ユニット/統合/契約/E2E）
2. `nix flake check` 緑
3. `policy/cue` 違反0
4. `contracts/` 差分なし

---

## 4. Ports & Adapters パターン

### Port（domains/*/ports/*.py）
```python
# domains/video/ports/storage.py
from abc import ABC, abstractmethod

class StoragePort(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> str:
        """Store data and return URL"""
        pass
```

**重要**: Portは同期定義を原則とする。非同期実行が必要な場合はAdapter側で吸収（内部でasyncio.run()等を使用）し、実行モデルをドメイン層に漏らさない。

### Adapter（infra/adapters/storage/*/）
```python
# infra/adapters/storage/r2/adapter.py
from domains.video.ports.storage import StoragePort
import asyncio

class R2StorageAdapter(StoragePort):
    def put(self, key: str, data: bytes) -> str:
        # 内部で非同期SDKを同期的にラップ
        return asyncio.run(self._put_async(key, data))

    async def _put_async(self, key: str, data: bytes) -> str:
        # R2 SDK呼び出し（非同期）
        pass
```

### DI（interfaces/*/wire.py）
```python
# interfaces/http-video-django/wire.py
from infra.adapters.storage.r2 import R2StorageAdapter
from apps.video.usecases import UploadVideoUseCase

def wire_upload_usecase() -> UploadVideoUseCase:
    storage_adapter = R2StorageAdapter()
    return UploadVideoUseCase(storage=storage_adapter)
```

---

## 5. CUEポリシ（構造ガード）

### policy/cue/rules/strict.cue
```cue
// 依存方向ガード
#DependencyDirection: {
    allowed: [
        "interfaces → apps",
        "interfaces → infra.runtimes",
        "apps → domains",
        "apps → infra.adapters",
        "domains → contracts",
    ]
    forbidden: [
        "domains → apps",
        "domains → interfaces",
        "domains → infra",
        "contracts → *",
    ]
}
```

### policy/cue/rules/no-deps-outside-infra.cue
```cue
// 依存宣言はinfra配下のみ
#DependencyDeclaration: {
    allowed_locations: [
        "infra/runtimes/*/constraints.txt",
        "infra/adapters/*/*/requirements.in",
    ]
    forbidden_locations: [
        "domains/**/requirements.txt",
        "apps/**/requirements.txt",
        "interfaces/**/requirements.txt",
    ]
}
```

### policy/cue/rules/forbidden-imports.cue
```cue
// domainsでの外部FW/SDK import禁止
#ForbiddenImports: {
    scope: "domains/**/*.py"
    forbidden: [
        "django",
        "fastapi",
        "requests",
        "sqlalchemy",
        "boto3",
        "google",
        "ffmpeg",
        "torch",
        "openai",
    ]
}
```

---

## 6. テスト階層

| 層 | テスト種別 | 実行場所 | モック対象 |
|----|----------|---------|-----------|
| **domains/** | ユニット | domains/*/tests/ | Port（抽象） |
| **apps/** | 統合 | apps/*/tests/ | Adapter（concrete） |
| **interfaces/** | 契約 | interfaces/*/tests/ | apps（実際のusecase） |
| **infra/adapters/** | 疎IT | infra/adapters/*/*/tests/ | 外部サービス（testcontainers等） |

---

## 7. 移行マッピング

| 旧パス（0.10.12） | 新パス（0.11.0） | 理由 |
|-----------------|----------------|------|
| `features/opencode-autopilot/` | `infra/adapters/opencode/autopilot/` | Port実装（外部システム） |
| `deployables/opencode-gateway/` | `interfaces/http-opencode-gateway/` | HTTPエントリポイント |
| `deployables/opencode-worker/` | `apps/video/workflows/` + `infra/adapters/queue/temporal/` | ワークフロー編成+実装分離 |
| `platform/temporal/` | `infra/adapters/queue/temporal/` | インフラAdapter |
| `platform/libsql/` | `infra/adapters/db/libsql/` | DB Adapter |

---

## 8. PRチェックリスト

### 再配置作業の必須確認

- [ ] `git log --stat` で関数/クラスシグネチャ変更がないか確認
- [ ] `git diff contracts/ssot/` が空であることを確認
- [ ] `git diff */constraints.txt */requirements.in` が infra/ 配下のみであることを確認
- [ ] 全テストが緑（ユニット/統合/契約/E2E）
- [ ] `nix flake check` が緑
- [ ] `policy/cue` 検証が違反0
- [ ] 旧→新パス対応表を添付

---

## 9. 代替案と却下理由

| 案 | 却下理由 |
|----|---------|
| ライブラリ全てinfra | ドメインロジックの純粋性を失う |
| 3層固定（MVC等） | 依存方向が不明確、テスタビリティ低下 |
| featuresに環境依存 | 結合増加、置換困難 |

---

## 10. リスク / 対策

| リスク | 対策 |
|-------|------|
| 移行時のimportパス変更漏れ | CI全緑必須、段階的PR |
| Port/Adapter境界の曖昧化 | CUEで構造ガード |
| infraの肥大化 | Adapter単位で分離、疎結合維持 |

---

## 11. 関連ADR

- **ADR 0.10.8**: SSOT-first & thin manifest（契約管理の基礎）
- **ADR 0.10.10**: Flake-driven manifest（決定的生成）
- **ADR 0.10.11**: consumes/Secrets/SBOM/CVE（セキュリティ強化）
- **ADR 0.10.12**: Orchestration v4.1b（本ADRにより Superseded）
- **ADR 0.11.0**: 本ADR（4層構成への統一リファクタ）

---

## 12. 完了条件（DoD）

1. 全ファイルが4層構造に再配置済み（git mv）
2. importパスが全て修正済み
3. flake出力名が命名規約に準拠（出力名=パス名）
4. `contracts/ssot/` に差分なし
5. 依存宣言が `infra/` 配下のみに集約
6. CI全緑（テスト/check/policy）
7. PR本文に旧→新パス対応表を添付
