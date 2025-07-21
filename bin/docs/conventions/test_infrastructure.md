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
| Python | `test_<target>.py` | `test_user_service.py` |
| TypeScript | `<target>.test.ts` | `user-service.test.ts` |
| Go | `<target>_test.go` | `user_service_test.go` |
| Rust | `mod.rs` 内の `#[cfg(test)]` | `tests/` ディレクトリ |

## テストランナー

### 標準テストランナー

| 言語 | ランナー | 実行コマンド |
|------|---------|-------------|
| Python | pytest | `pytest` |
| TypeScript | node:test / deno test | `npm test` / `deno test` |
| Go | go test | `go test ./...` |
| Rust | cargo test | `cargo test` |

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