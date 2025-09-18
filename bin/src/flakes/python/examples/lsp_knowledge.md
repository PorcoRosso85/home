# Python LSP知見：pyright & ruff

このドキュメントは、知識共有の設計原則に基づいて、pyrightとruffのLSP機能に関する実践的な知見を共有します。

## 発見可能な知識

### 1. インポートパスのリファクタリング

#### 🔍 発見：絶対パス vs 相対パス

```bash
# 絶対インポートの検証
nix develop -c pyright examples/absolute_imports/

# 相対インポートの検証
nix develop -c pyright examples/relative_imports/
```

**学習ポイント**：
- pyrightは両方のインポートスタイルを正しく解析
- プロジェクトルートの設定が重要（pyproject.toml）
- 相対インポートは`__init__.py`の存在が必須

### 2. LSPサーバーの起動

#### pyright LSP

```bash
# LSPサーバーとして起動
nix develop -c pyright --langserver --stdio

# 診断情報をJSON形式で取得
nix develop -c pyright --outputjson <path>
```

#### ruff serve

```bash
# Ruff LSPサーバーの起動
nix develop -c ruff serve

# デフォルトポート: 4797
# カスタムポート: ruff serve --port 8080
```

### 3. エラーメッセージから学ぶ

#### インポートエラーの例

```python
# test_import_error.py
from examples.absolute_imports.domain.nonexistent import Something
```

pyrightの教育的なエラー：
```
error: Import "examples.absolute_imports.domain.nonexistent" could not be resolved
```

**学習機会**：
- モジュールパスの構造を理解
- Pythonのパッケージ解決メカニズム
- `PYTHONPATH`と`sys.path`の関係

### 4. 段階的な学習パス

#### レベル1：基本的な型チェック

```bash
# 単一ファイルの型チェック
nix develop -c pyright your_file.py
```

#### レベル2：プロジェクト全体の解析

```bash
# プロジェクト全体を解析
nix develop -c pyright .

# 設定ファイルを使用
echo '{"include": ["src"], "strict": ["src/domain"]}' > pyproject.toml
```

#### レベル3：LSP統合

```vim
" Neovimでの設定例
lua << EOF
require'lspconfig'.pyright.setup{
  cmd = {"nix", "develop", "-c", "pyright-langserver", "--stdio"}
}
EOF
```

### 5. 実験による発見

#### pyrightの設定探索

```bash
# 利用可能なオプションを発見
nix develop -c pyright --help

# 設定の優先順位を理解
# 1. コマンドライン引数
# 2. pyproject.toml
# 3. pyrightconfig.json
```

#### ruffの機能探索

```bash
# 利用可能なルールを発見
nix develop -c ruff rule --all

# 特定のルールの説明
nix develop -c ruff rule E501  # 行の長さ
```

## 組み合わせ可能なパターン

### パターン1：型チェックとフォーマット

```bash
# 型チェック → フォーマット → 再チェック
nix develop -c pyright . && \
nix develop -c ruff check --fix . && \
nix develop -c pyright .
```

### パターン2：インクリメンタルな移行

```python
# migration_helper.py
import subprocess
import json

def check_imports(path):
    """インポートスタイルをチェック"""
    result = subprocess.run(
        ["pyright", "--outputjson", path],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    return data.get("generalDiagnostics", [])
```

### パターン3：CI統合

```nix
# flake.nix のアプリ定義
apps.check-python = {
  type = "app";
  program = toString (pkgs.writeShellScript "check-python" ''
    ${pkgs.pyright}/bin/pyright . || exit 1
    ${pkgs.ruff}/bin/ruff check . || exit 1
    echo "✅ All checks passed!"
  '');
};
```

## トラブルシューティング

### よくある問題と解決策

#### Q: pyrightが相対インポートを解決できない

```bash
# 診断コマンド
find . -name "__init__.py" | head -10
python -c "import sys; print(sys.path)"
```

**解決策**：
1. `__init__.py`ファイルの確認
2. PYTHONPATHの設定
3. パッケージとして実行（`python -m`）

#### Q: ruff serveが起動しない

```bash
# ポートの確認
lsof -i :4797

# 別ポートで起動
nix develop -c ruff serve --port 8888
```

## 継続的な発見

### 実験用スクリプト

```bash
# explore_lsp.sh
#!/usr/bin/env bash
echo "🔍 Discovering LSP capabilities..."

# pyrightの機能を探索
echo "Pyright version:"
pyright --version

echo -e "\nAvailable pyright options:"
pyright --help | grep -E "^\s+--" | head -10

# ruffの機能を探索
echo -e "\nRuff version:"
ruff --version

echo -e "\nRuff LSP features:"
ruff serve --help | grep -E "^\s+--"
```

### 知識の更新

新しい発見があれば、以下の形式で追加：

```markdown
#### 🆕 発見日: YYYY-MM-DD
**発見内容**: 具体的な発見
**再現方法**: `コマンド例`
**活用方法**: 実践的な使い方
```

## 関連リソース

- `examples/absolute_imports/` - 絶対インポートの例
- `examples/relative_imports/` - 相対インポートの例
- `examples/lsp_refactoring_demo.py` - リファクタリングデモ
- `/home/nixos/bin/docs/conventions/knowledge_sharing.md` - 知識共有の原則