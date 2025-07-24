# テストインフラストラクチャ規約

> 📚 関連ファイル
> - テスト哲学 → [testing.md](./testing.md)
> - TDDプロセス → [tdd_process.md](./tdd_process.md)
> - このファイルはテスト実行環境の技術的詳細を定義

## ファイル配置と命名規則

### テストファイルの配置
- **原則**: テスト対象と同じディレクトリに配置する
- **理由**: テストとコードの関連性を明確にし、メンテナンス性を向上

### ファイル命名規則

| 言語 | テストファイル名 | 例 |
|------|-----------------|-----|
| Python | `test_<対象ファイル名>.py` | `test_vss_service.py` (vss_service.pyのテスト) |
| TypeScript | `<対象ファイル名>.test.ts` | `vssService.test.ts` |
| Go | `<対象ファイル名>_test.go` | `vss_service_test.go` |
| Rust | `mod.rs` 内の `#[cfg(test)]` | `tests/` ディレクトリ |

> 💡 テスト対象ファイルとの1対1対応により、テストの発見性と保守性を向上

### 関数命名規則

テスト関数は、動くドキュメントとして仕様を説明する名前にする：

| 言語 | テスト関数名 | 例 |
|------|-------------|-----|
| Python | `def test_<何を_どうすると_どうなる>()` | `def test_vector_search_with_similar_query_returns_relevant_documents()` |
| TypeScript | `test('<仕様の説明>', ...)` | `test('vector search with similar query returns relevant documents', ...)` |
| Go | `func Test<WhatWhenThen>(t *testing.T)` | `func TestVectorSearchWithSimilarQueryReturnsRelevantDocuments(t *testing.T)` |
| Rust | `fn test_<what_when_then>()` | `fn test_vector_search_with_similar_query_returns_relevant_documents()` |

> 💡 関数名で仕様を表現し、テストが何を保証するかを明確にする → [testing.md](./testing.md)

## テストランナー

### 標準テストランナー

| 言語 | ランナー | 実行コマンド | 使用場面 |
|------|---------|-------------|----------|
| Python | pytest | `pytest` | E2Eテスト（全言語共通）、Python実装の単体・統合テスト |
| TypeScript | node:test / deno test | `npm test` / `deno test` | TypeScript実装の単体・統合テスト |
| Go | go test | `go test ./...` | Go実装の単体・統合テスト |
| Rust | cargo test | `cargo test` | Rust実装の単体・統合テスト |

> 💡 E2Eテストは言語を問わずpytestで統一。統合・単体テストは実装言語と同じものを使用。

### Nix統合

すべてのプロジェクトは `nix run .#test` で統一的にテストを実行できるようにする：

```nix
# flake.nix
{
  apps.${system}.test = {
    type = "app";
    program = "${pkgs.writeShellScript "test" ''
      # 言語に応じたテストコマンド
      ${testCommand}
    ''}";
  };
}
```

## テスト環境設定

### 環境変数
- `TEST_ENV=true`: テスト実行中であることを示す
- `CI=true`: CI環境での実行を示す（該当する場合）

### タイムアウト設定
- 単体テスト: 5秒以内
- 統合テスト: 30秒以内
- E2Eテスト: 5分以内

### 並列実行
- 可能な限り並列実行を有効にする
- テスト間の依存関係を排除する
- 共有リソースへのアクセスを避ける

## CI/CD統合

### GitHub Actions例
```yaml
- name: Run tests
  run: nix run .#test
```

### 必須チェック
- すべてのテストがパスすること
- カバレッジが閾値を満たすこと（新規コード80%以上）
- テスト実行時間が妥当であること

## E2Eテスト構造

### ディレクトリ構成
E2Eテストは、テスト対象の範囲に応じて`e2e/`ディレクトリ内で構造化する：

```
e2e/
├── internal/      # 内部E2Eテスト
│   └── test_e2e_*.py
└── external/      # 外部パッケージテスト
    ├── flake.nix
    └── test_e2e_*.py
```

### internal（内部E2Eテスト）
- **対象**: 同一flake内でのエンドツーエンド動作
- **内容**: CLIコマンド実行、API呼び出し、エラーハンドリング
- **実行**: メインのテストスイートの一部として実行
- **例**: ユーザーワークフロー、コマンドチェーン、設定ファイル処理

### external（外部パッケージテスト）
- **対象**: 他のflakeから依存パッケージとして利用される場合の動作
- **内容**: パッケージのimport、公開APIの契約、型情報の正確性
- **実行**: 独立したflakeとして別プロセスで実行
- **例**: `from package import PublicAPI`の動作確認

### テスト実装例

#### Internal E2Eテスト
```python
# e2e/internal/test_e2e_search_workflow.py
def test_e2e_vector_search_complete_workflow():
    """ベクトル検索の完全なワークフローをテスト"""
    # 1. データベース初期化
    result = subprocess.run(["nix", "run", ".#init-db"], ...)
    
    # 2. データ投入
    result = subprocess.run(["nix", "run", ".#load-data"], ...)
    
    # 3. 検索実行
    result = subprocess.run(["nix", "run", ".#search", "--query", "test"], ...)
    
    # 4. 結果検証
    assert "expected_result" in result.stdout
```

#### External E2Eテスト
```nix
# e2e/external/flake.nix
{
  inputs.target-package.url = "path:../..";
  
  outputs = { self, target-package, ... }: {
    apps.test = {
      type = "app";
      program = "${pkgs.writeShellScript "test-external" ''
        ${pythonEnv}/bin/pytest -v test_e2e_*.py
      ''}";
    };
  };
}
```

```python
# e2e/external/test_e2e_import.py
def test_e2e_package_can_be_imported():
    """パッケージが外部から正しくimportできることを確認"""
    import vss_kuzu
    assert hasattr(vss_kuzu, '__version__')
    assert callable(vss_kuzu.search)
```

### 実行コマンドの統合
```nix
# flake.nix
apps.test = {
  type = "app";
  program = "${pkgs.writeShellScript "test" ''
    # ユニット・統合テスト
    ${pythonEnv}/bin/pytest -v src/
    
    # 内部E2Eテスト
    [ -d "e2e/internal" ] && ${pythonEnv}/bin/pytest -v e2e/internal/
    
    # 外部E2Eテスト
    [ -f "e2e/external/flake.nix" ] && (cd e2e/external && nix run .#test)
    
    # 警告表示
    [ ! -d "e2e/internal" ] && echo "⚠️  WARNING: No internal E2E tests"
    [ ! -d "e2e/external" ] && echo "⚠️  WARNING: No external E2E tests"
  ''}";
};
```

## テストデータ管理

### フィクスチャ
- `fixtures/` ディレクトリに配置
- 最小限のデータセットを使用
- 実データのサニタイズ版を使用

### モックとスタブ
- 外部サービスとの通信は必ずモック
- 時刻依存のテストは時刻を固定
- ランダム値は固定シードを使用

## トラブルシューティング

### よくある問題
1. **環境依存の失敗**: 環境変数の設定を確認
2. **タイミング依存**: 非同期処理の適切な待機を追加
3. **順序依存**: テストの独立性を確保

### デバッグ手法
- `--verbose` フラグでログ詳細を表示
- 単一テストの実行でイsolate
- テスト前後の状態を出力