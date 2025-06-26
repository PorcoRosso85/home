# テスト実行ガイド

## 概要

このプロジェクトでは、t-wada TDDスタイルのin-sourceテストを採用しています。
各モジュール内にテスト関数が定義されており、pytestで一括実行できます。

## テスト実行方法

```bash
# requirement/graphディレクトリで実行
LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ uv run --with pytest pytest
```

オプション:
- `-v`: 詳細表示
- `-x`: 最初の失敗で停止
- `-k "test_name"`: 特定のテストのみ実行
- `-q`: 静かなモード

例：
```bash
# 特定のテストのみ実行
LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ uv run --with pytest pytest -k test_create_decision

# 詳細表示で実行
LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ uv run --with pytest pytest -v

# 静かなモードで実行
LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ uv run --with pytest pytest -q
```

## テスト構成

- **テスト総数**: 98個（2025年6月現在）
- **成功率**: 約81.6%
- **テストファイル形式**: 各モジュール内にtest_で始まる関数として定義

### テスト命名規則

t-wada TDDスタイルに従い、以下の形式で命名:
```
test_{対象関数}_{条件}_{期待結果}
```

例:
- `test_create_decision_valid_input_returns_decision_object`
- `test_validate_no_circular_dependency_with_cycle_returns_error`

## 環境設定

### LD_LIBRARY_PATH

KuzuDBを使用するテストでは、LD_LIBRARY_PATHの設定が必要です。
テストスクリプトで自動設定されますが、手動実行時は以下を設定:

```bash
export LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/
```

## トラブルシューティング

### ImportError

相対インポートエラーが発生する場合は、親ディレクトリから実行してください:
```bash
cd /home/nixos/bin/src
pytest requirement/graph
```

### KuzuDB関連エラー

LD_LIBRARY_PATHが正しく設定されているか確認してください。