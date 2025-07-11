# Search POC テストガイド

## テスト実行方法

### 全テスト実行（推奨）
```bash
cd /home/nixos/bin/src/poc/search
nix run .#test
```

### 個別テスト実行
```bash
# 仕様テストのみ
nix run .#test-spec

# 統合テストのみ  
nix run .#test-integration

# リントチェック
nix run .#lint

# フォーマット
nix run .#format
```

## テストの種類と目的

### 1. 仕様テスト（Specification Tests）
- **ファイル**: 
  - `test_search_poc_spec.py` - POC全体の仕様
  - `test_kuzu_native_spec.py` - KuzuDB機能の仕様
- **特徴**: 実行可能なドキュメントとして機能
- **状態**: 8 passed, 8 skipped

### 2. 統合テスト（Integration Tests）
- **ファイル**:
  - `test_kuzu_vss_fts_integration.py` - VSS/FTS統合
  - `test_requirement_search_integration.py` - 要件検索統合
- **特徴**: KuzuDB実機能のテスト
- **注意**: numpy依存があるため、vss機能利用時にエラーになる場合がある

### 3. E2Eテスト（End-to-End Tests）
- **ファイル**: `test_hybrid_search_e2e.py`
- **特徴**: 実際のユースケースシナリオ
- **状態**: 2/3 シナリオ成功

## 依存関係の問題

現在、`vss`モジュールがnumpyに依存しているため、一部のテストが失敗します。
これは`embeddings` POCとの統合時に解決予定です。

## 規約遵守

- **実行方法**: `nix run .#test`のみ使用
- **直接実行禁止**: `python`や`pytest`コマンドの直接使用は禁止
- **環境**: requirement/graphの仮想環境を使用

## トラブルシューティング

### エラー: "No module named 'numpy'"
vssモジュールの依存関係エラーです。仕様テストには影響しません。

### エラー: "requirement/graphの仮想環境が見つかりません"
requirement/graphで先にセットアップを実行してください。

## 今後の改善点

1. numpy依存の解決（embeddings POCとの統合）
2. KuzuDB拡張機能の実装待ち
3. モック実装の本番実装への置き換え