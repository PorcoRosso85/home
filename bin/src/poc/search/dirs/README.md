# Directory Scanner with Search

動的にディレクトリ構造をスキャンし、FTS/VSSで検索可能にするツール

## 特徴

- 差分検知によるインクリメンタル更新
- FTS（Full Text Search）による高速キーワード検索
- VSS（Vector Similarity Search）による意味的検索
- メタデータ自動抽出（README, flake.nix, package.json）
- In-memoryモード対応

## 使用方法

このツールは`nix develop`環境でのみ動作します。

### セットアップ

```bash
# 開発環境に入る
nix develop

# 依存関係をインストール
uv sync
```

### アプリケーション実行

```bash
# nix develop環境内で実行
uv run dirscan scan
uv run dirscan search "query"
uv run dirscan status

# または直接実行
nix develop -c uv run dirscan scan
```

### テスト実行

```bash
# nix develop環境内で実行
uv run pytest

# 特定のテストのみ
uv run pytest test_unit.py
uv run pytest -k "test_is_hidden"

# または直接実行
nix develop -c uv run pytest
```

### 環境変数

開発環境では以下がデフォルト設定されます：
- `DIRSCAN_ROOT_PATH`: カレントディレクトリ
- `DIRSCAN_DB_PATH`: `:memory:`
- `DIRSCAN_INMEMORY`: `true`

## 開発状況

- [x] TDD Red Phase: テスト作成
- [x] TDD Green Phase: 実装完了
- [x] 規約準拠: 完全準拠