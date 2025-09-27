# CUE Contract Management System

## 目的

CUEをSingle Source of Truth（SSOT）とした強制ゲートにより、複数flakeの齟齬なき増加を機械的に担保する。人の記憶や手順に依存せず、CI/フックで強制的にコンプライアンスを保証する。

## スコープと制約

### 追跡対象（固定）
- **対象**: `contracts/**/contract.cue` のみ
- **排他**: `index.gen.cue` の手作成・コミットは禁止（Nix派生のみ）
- **前提**: CUE v0.6系、Nix flakes、有効な `cue.mod` のvendor固定

### 一意性ルール
- **一意キー**: `namespace + name` でレポジトリ全体の重複禁止
- **namespace規約**: 逆ドメイン形式推奨（例: `corp.example`）
- **文字制限**: 小文字・数字・ハイフン・ドットのみ

## 基本原則

### 1. 閉鎖スキーマ原則
- 未定義フィールド禁止（closed struct）
- `role` と `provides/dependsOn` を型付きで必須

### 2. 派生物原則
- 下流は CUE export の JSON のみ入力可
- 手書き値の注入は禁止

### 3. Vendor固定原則
- CUE モジュールは vendor 固定
- 更新は PR 経由のみ

### 4. CI前提原則
- すべての検査を `nix flake check` で実行
- `--impure` 実行は禁止

## 実装状況 ✅ ENHANCED

**条件付きバリデーション機能の実装完了:**

- ✅ **条件付きバリデーション**: ディレクトリごとに異なる検査レベル
- ✅ **本番環境検査**: `contracts/production/` での厳格バリデーション
- ✅ **サンプル検査**: `contracts/examples/` での教育的バリデーション
- ✅ **テスト検査**: `contracts/test/` での構文のみバリデーション
- ✅ **並列実行**: 各検査タイプの独立並列実行
- ✅ CUE schema foundation with closed structures and versioning
- ✅ File enumeration with pure eval and stable sorting
- ✅ Directory-aware aggregation checks with standardized messages
- ✅ Multiple validation pipeline integration with fixed naming
- ✅ Secrets management with SOPS support and plaintext detection
- ✅ Pre-commit integration with fixed hooks
- ✅ Separated examples (basic/anti-patterns) for educational purposes
- ✅ Comprehensive migration documentation

## Quick Start

```bash
# 1. Enter development environment
nix develop

# 2. Run all validations
nix flake check

# 3. Install pre-commit hooks
pre-commit install

# 4. Start developing (see docs/NEW_DEVELOPER_GUIDE.md)
```

## Documentation

- 📖 **[New Developer Guide](docs/NEW_DEVELOPER_GUIDE.md)** - Complete getting started guide
- 📋 **[Contract Examples](contracts/examples/README.md)** - Validation examples (basic/anti-patterns)
- 🔧 **[Testing Scripts](tools/)** - Automated test suite
  - `test-secrets.sh` - Secrets detection validation
  - `test-precommit.sh` - Pre-commit hooks testing
  - `test-examples.sh` - Contract validation examples

## 開発フロー

```
1. nix develop でプロジェクト環境に入る
2. contract.cue を記述（閉鎖・責務・依存を満たす）
3. pre-commit 実行（fmt/vet/check/平文検出）
4. PR 作成
5. CI が全ゲート実施
6. 全通過でマージ
```

## 検査項目

### 必須チェック（条件付きバリデーション）
- `checks.<system>.cueFmt`: `cue fmt ./...` の差分ゼロ
- `checks.<system>.cueVet`: `cue vet ./...` エラーゼロ
- `checks.<system>.cueExport`: `cue export ./...` 成功
- `checks.<system>.contractsProduction`: **厳格検査** - 本番契約の完全バリデーション
- `checks.<system>.contractsExamples`: **教育検査** - サンプル契約の構文チェック
- `checks.<system>.contractsTest`: **最小検査** - テスト用契約の構文のみ
- `checks.<system>.secretsPlaintext`: 平文シークレット検出ゼロ
- `checks.<system>.systemdVerify`: systemd-analyze verify 成功
- `nixosTests.smoke`: 最小スモーク（起動/ユニット/ポート）

### 条件付きバリデーション詳細

| ディレクトリ | 検査レベル | 目的 | 失敗許容度 |
|-------------|-----------|------|-----------|
| `contracts/production/` | **厳格** | 本番運用契約 | ゼロ許容 |
| `contracts/examples/` | **教育的** | 学習・デモ | エラー想定 |
| `contracts/test/` | **構文のみ** | テストフィクスチャ | 検査無効化 |

### Pre-Commit（ローカル必須）
- `cue fmt`, `cue vet`
- `nix flake check -L`
- 平文秘密検出
- `shfmt/shellcheck`（スクリプトがある場合）

## 契約スキーマ

### 必須フィールド
```cue
{
    namespace: string  // 逆ドメイン形式
    name: string      // プロジェクト名
    role: "service"|"lib"|"infra"|"app"|"tool"
    provides: [...Capability]
    dependsOn: [...CapabilityRef]
    // 追加フィールドは禁止（closed）
}
```

### Capability定義
```cue
Capability: {
    kind: "http"|"db"|"queue"|...
    id?: string
    version?: semver
    port?: int & >=1 & <=65535
    protocol?: "tcp"|"udp"|"http"|"grpc"
    scope?: "internal"|"public"
}
```

### CapabilityRef定義
```cue
CapabilityRef: {
    kind: string
    target: string  // namespace/name
    id?: string
    versionRange?: string  // semver range
}
```

## 期待される失敗例

### 重複名
```
aggregate: duplicate namespace/name found in [contracts/api, contracts/gateway]
```

### 未解決依存
```
deps: missing provider for 'corp.example/db#postgres:primary' (required by corp.example/api)
```

### スキーマ違反
```
schema: provides[0].port: 70000 out of range (1..65535)
```

### 閉鎖構造違反
```
schema: additional field "debugFlag" not allowed (closed struct)
```

### 契約ファイル未設置
```
discovery: contract.cue not found under contracts/*: [contracts/new-svc]
```

### 平文シークレット
```
secrets: plaintext detected in secrets/prod.yaml (keys: password, token)
```

### 成功例
```
all checks passed: cue fmt/vet/export, aggregate, nixosTests, secrets
```

## Secrets運用

### 必須ルール
- `secrets/**` は暗号化必須
- `sops-nix` と `.sops.yaml` を必須化
- 平文検出キー: `password`, `token`, `private_key`, `aws_secret_access_key` 等
- 例外: `.example` 拡張子のドキュメント用ダミー値のみ許容

## Definition of Done

すべての項目が通過すること：

- [ ] **CUEゲート**: `cue fmt/vet/export` 成功
- [ ] **存在強制**: `contracts/**/contract.cue` 欠落ゼロ
- [ ] **集約検査**: 一意性/依存関係/責務衝突ゼロ
- [ ] **Secrets**: 平文検出ゼロ＋sops参照可能
- [ ] **実行性**: nixosTests と systemd-analyze verify 成功
- [ ] **ガバナンス**: Pre-Commit/CI/lock監視、`--impure` 禁止が常時有効

## FAQ

### Q: namespace の命名規則は？
A: 逆ドメイン形式推奨（例: `corp.example.api`）。小文字・数字・ハイフン・ドットのみ。

### Q: capability キーの形式は？
A: `namespace/name#kind[:id]`（例: `corp.example/api#http:public`）

### Q: 依存関係の解決範囲は？
A: 単一リポジトリ内のみ。inputs 横断は将来スコープ。

### Q: 破壊変更の定義は？
A: 必須フィールド削除、型の狭め、列挙縮小、範囲狭め、既存capability削除。

### Q: vendor更新の手順は？
A: `cue mod vendor` 更新は PR 経由のみ。`cue.mod` と `cue.mod/pkg` をコミット。

## ディレクトリ構成

```
.
├── schema/              # 共通CUEスキーマ
├── contracts/           # 条件付きバリデーション対応
│   ├── production/      # 本番契約（厳格検査）
│   │   ├── api/contract.cue
│   │   ├── database/contract.cue
│   │   └── cache/contract.cue
│   ├── examples/        # 教育用契約（寛容検査）
│   │   ├── basic/contract.cue
│   │   └── anti-patterns/
│   │       ├── duplicates/     # 重複検出デモ
│   │       └── unresolved-deps/ # 依存解決エラーデモ
│   └── test/            # テスト用契約（構文のみ）
│       └── fixtures/
├── tools/              # 集約CUE・補助スクリプト
├── secrets/            # sops対象（.sops.yaml必須）
├── baseline/           # 旧export（SemVer検査用）
├── tests/nixos/        # 最小スモークテスト
├── docs/               # 実装ドキュメント
│   ├── architecture-separation.md
│   └── implementation-options.md
├── .pre-commit-config.yaml
├── .sops.yaml
├── cue.mod
├── flake.nix
└── flake.lock
```

## 実行コマンド

### 開発時
```bash
# 開発環境起動
nix develop

# フォーマット
cue fmt ./...

# 検証
cue vet ./...

# エクスポート
cue export ./...

# 条件付きバリデーション実行
nix build .#checks.x86_64-linux.contractsProduction  # 本番契約のみ
nix build .#checks.x86_64-linux.contractsExamples    # サンプル契約のみ
nix build .#checks.x86_64-linux.contractsTest        # テスト契約のみ

# 全チェック（並列実行）
nix flake check -L --pure-eval --no-write-lock-file

# Pre-commit
pre-commit run --all-files
```

### マイグレーション手順

既存の単一バリデーションシステムからの移行:

```bash
# 1. 本番契約の移動
mkdir -p contracts/production
mv contracts/existing-service contracts/production/

# 2. サンプル契約の整理
mkdir -p contracts/examples/basic contracts/examples/anti-patterns
mv contracts/examples/normal/* contracts/examples/basic/
mv contracts/examples/duplicate contracts/examples/anti-patterns/duplicates
mv contracts/examples/unresolved contracts/examples/anti-patterns/unresolved-deps

# 3. テスト契約の分離
mkdir -p contracts/test/fixtures
mv test-contracts/* contracts/test/fixtures/

# 4. 権限修正（必要に応じて）
chmod -R +r contracts/

# 5. 個別バリデーション確認
nix build .#checks.x86_64-linux.contractsProduction
```

### CI/CD
```bash
# CI推奨コマンド
nix --extra-experimental-features nix-command \
    --extra-experimental-features flakes \
    flake check --no-write-lock-file --pure-eval -L
```

---

**注意**: この README は CUE Contract Management System の完全な仕様書です。すべての規約を機械的に強制し、人的ミスを排除します。