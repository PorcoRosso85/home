# 開発ガイド

## 原則: nix develop環境でのみ動作

このプロジェクトは一貫性のため、`nix develop`環境でのみ動作するよう設計されています。

## 動作確認

### 1. 直接実行の禁止

```bash
# これらは全て失敗します（意図的）
python main.py         # → エラー: CLI経由で実行してください
python test_unit.py    # → エラー: pytestがありません
pytest                 # → エラー: コマンドが見つかりません
```

### 2. 正しい実行方法

```bash
# 開発環境に入る
nix develop

# 依存関係のインストール
uv sync

# アプリケーション実行
uv run dirscan scan
uv run dirscan search "keyword"

# テスト実行
uv run pytest
uv run pytest -v
uv run pytest test_unit.py::TestUtilityFunctions
```

### 3. ワンライナー実行

```bash
# 開発環境に入らずに実行
nix develop -c uv run dirscan scan
nix develop -c uv run pytest
```

## ファイル構成

- `flake.nix`: Nix開発環境定義
- `pyproject.toml`: Python依存関係とpytest設定
- `conftest.py`: pytestフィクスチャ
- `test_*.py`: テストファイル（直接実行不可）
- `main.py`, `cli.py`: アプリケーションコード（直接実行不可）

## 環境変数

`nix develop`で自動設定される：
- `DIRSCAN_ROOT_PATH`: カレントディレクトリ
- `DIRSCAN_DB_PATH`: `:memory:`
- `DIRSCAN_INMEMORY`: `true`

## 注意事項

- `nix run`コマンドは使用しません（エラーメッセージのみ表示）
- 全ての実行は`nix develop`環境内で`uv run`経由で行います
- テストは`pytest`を直接ではなく`uv run pytest`で実行します