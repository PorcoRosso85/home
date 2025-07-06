# KuzuDB Database Factory Segfault Investigation POC

## 概要
requirement/graphプロジェクトで発生しているdatabase_factory関連のセグフォルト問題を調査・解決するためのPOC。

## 問題の症状
- `test_database_factory.py::TestDatabaseFactory::test_create_persistent_database`でセグフォルト発生
- 単独実行では問題なし
- 全テスト実行時のみ発生（実行順序依存の可能性）

## 調査対象
1. `importlib.reload(kuzu)`の影響
2. pytest実行順序による干渉 
3. KuzuDBインスタンスの複数作成時の問題
4. nix環境特有の問題
5. LD_LIBRARY_PATHの設定問題

## ディレクトリ構成
```
.
├── README.md                    # このファイル
├── flake.nix                   # Nix環境定義
├── pyproject.toml              # Python依存関係
├── test_segfault_minimal.py    # 最小再現テスト
├── test_import_reload.py       # importlib.reload調査
├── test_multiple_instances.py  # 複数インスタンス作成テスト
└── test_execution_order.py     # 実行順序依存性テスト
```

## 実行方法
```bash
# Nix環境でのテスト実行
nix run .#test

# 個別テスト実行
nix run .#test -- test_segfault_minimal.py -v

# デバッグモード
nix run .#test -- --pdb
```

## 期待される成果
1. セグフォルトの根本原因の特定
2. 安定した回避策の実装
3. requirement/graphプロジェクトへの修正適用