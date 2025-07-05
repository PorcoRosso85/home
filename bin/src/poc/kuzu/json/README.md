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

## JSON型の使用について

現在の実装は**JSON型を使用**するよう更新されています：
- `CREATE NODE TABLE` で `JSON` 型カラムを定義
- `to_json()` 関数でJSON型データを挿入
- `json_extract()`, `json_merge_patch()` などのJSON関数を使用

## Segfault回避の工夫

`bin/src/requirement/graph`の調査から、以下のsegfault回避策を実装しています：

### 1. データベースファクトリーパターン
- インスタンスの一元管理
- テスト用ユニークインスタンス生成
- モジュールの自動リロード

### 2. 自動クリーンアップ（conftest.py）
- 各テスト前後でキャッシュクリア
- kuzu モジュールのリロード
- JSON拡張機能の状態リセット

### 3. テンポラリディレクトリの使用
- インメモリではなく実ファイルシステムを使用
- テスト間の状態汚染を防止

### 4. JSON Extension Manager
- 拡張機能の読み込み状態を管理
- 重複読み込みを防止
- スレッドローカルストレージで状態管理

