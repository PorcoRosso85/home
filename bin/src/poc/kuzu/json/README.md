# KuzuDB JSON POC

KuzuDBのJSON拡張機能を使用したPOC実装。

## 概要

KuzuDBのJSON機能を実装：
- JSONデータ型のサポート
- JSON関数（to_json, json_extract, json_merge_patch等）
- エラーを値として返すパターン
- 純粋関数とアダプターの分離

## ディレクトリ構造

```
kuzu_json_poc/
├── __init__.py    # パブリックAPI
├── types.py       # 型定義
├── core.py        # 純粋関数（JSONデータ操作）
└── adapters.py    # KuzuDB統合（副作用）

test_*.py          # pytestテストファイル
```

## 実行方法

```bash
# テスト実行
nix run .#test

# デモ実行
nix run .#demo

# 特定のテストのみ実行
nix run .#test -- -k "test_validate_json"

# 開発環境に入る
nix develop

# 開発環境内でのコマンド
uv sync              # 依存関係インストール
uv run pytest -v     # テスト実行
ruff check .         # リントチェック
ruff format .        # フォーマット
```

## 技術仕様

### 依存関係
- Python 3.11+
- KuzuDB 0.10.1+
- pandas（DataFrameサポート用）
- pytest（テスト実行）

### エラーハンドリング
すべての関数はエラーを値として返します：

```python
Union[SuccessType, ErrorDict]

ErrorDict = TypedDict({
    "error": str,
    "details": Optional[str],
    "traceback": Optional[str]
})
```

## テスト

- `test_core.py` - 純粋関数のテスト（22個）
- `test_adapters.py` - KuzuDB統合テスト（9個）
- `test_integration.py` - 統合テスト（4個）

```bash
# すべてのテストを実行
nix run .#test
```