# ファイル命名規約

## 原則

**言語固有の慣習を尊重** - 各プログラミング言語のコミュニティで確立された命名規則に従う

## 言語別ファイル命名規則

### TypeScript/JavaScript
- **通常ファイル**: `camelCase.ts` / `camelCase.js`
  - 例: `websocketSync.ts`, `conflictResolver.ts`, `metricsCollector.ts`
- **クラス/コンポーネント**: `PascalCase.ts` （主要エクスポートがクラスの場合）
  - 例: `UserService.ts`, `DatabaseConnection.ts`
- **型定義ファイル**: `types.ts` または `<機能名>Types.ts`
  - 例: `types.ts`, `userTypes.ts`

### Python
- **通常ファイル**: `snake_case.py`
  - 例: `websocket_sync.py`, `conflict_resolver.py`, `metrics_collector.py`
- **定数ファイル**: `constants.py` または `<機能名>_constants.py`

### Go
- **通常ファイル**: `snake_case.go`
  - 例: `websocket_sync.go`, `conflict_resolver.go`

### Rust
- **通常ファイル**: `snake_case.rs`
  - 例: `websocket_sync.rs`, `conflict_resolver.rs`

## 特殊ケース

### CLIエントリーポイント
- **kebab-case** を使用可能（シェルコマンドとの親和性）
  - 例: `websocket-server.ts` (CLIとして実行される場合)

### 設定ファイル
- **言語/ツール固有の慣習に従う**
  - `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`
  - `deno.json`, `tsconfig.json`, `.prettierrc`

## 言語混在プロジェクトでの扱い

同一ディレクトリに複数言語のファイルが存在する場合：

```
unified/
├── websocketSync.ts      # TypeScript: camelCase
├── websocket_sync.py     # Python: snake_case
├── websocket_sync.go     # Go: snake_case
└── websocket_sync.rs     # Rust: snake_case
```

**重要**: 同じ機能でも、各言語の慣習に従った命名を使用する

## 移行戦略

既存プロジェクトでの適用：

1. **新規ファイル**: この規約に従って命名
2. **既存ファイル**: 大規模リファクタリング時に段階的に移行
3. **外部API影響**: インターフェースに影響する場合は慎重に検討

## アンチパターン

- ❌ 言語に関わらず統一的な命名（例: 全てsnake_case）
- ❌ ファイル名に言語サフィックス（例: `parser_ts.ts`, `parser_py.py`）
- ❌ 過度に長いファイル名（30文字以上）
- ❌ 特殊文字の使用（`-` と `_` 以外）

## 関連規約

- [パッケージ命名規約](./package_naming.md) - パッケージレベルの命名
- [モジュール設計](./module_design.md) - ディレクトリ構造とファイル配置
- [テストインフラ](./test_infrastructure.md) - テストファイルの組織化とベストプラクティス