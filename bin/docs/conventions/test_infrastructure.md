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
| TypeScript | `<対象ファイル名>.test.ts` | `vss-service.test.ts` |
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