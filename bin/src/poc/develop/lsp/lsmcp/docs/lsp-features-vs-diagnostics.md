# LSP機能 vs 診断ツールの違い

## 今回実装したもの（診断ツール）
- ❌ 変数の参照検索
- ❌ 定義へジャンプ
- ❌ シンボル検索
- ✅ エラーチェック（構文、型、スタイル）

## LSMCPが本来提供するLSP機能

### 1. 参照検索（Find References）
```bash
# MCPサーバー経由での使用例
mcp__python__lsmcp_find_references "Calculator" 15 10
```
→ `Calculator`クラスが使われているすべての場所を検索

### 2. 定義へ移動（Go to Definition）
```bash
mcp__python__lsmcp_get_definitions "add" 20 15
```
→ `add`メソッドが定義されている場所を特定

### 3. ホバー情報（型情報・ドキュメント）
```bash
mcp__python__lsmcp_get_hover 10 20
```
→ カーソル位置の変数/関数の型情報を表示

### 4. シンボル一覧
```bash
mcp__python__lsmcp_get_document_symbols
```
→ ファイル内のすべてのクラス、関数、変数をリスト

## PythonでLSP機能を使うには

### 方法1: LSMCPをMCPサーバーとして起動
```bash
# .mcp.jsonに設定
{
  "mcpServers": {
    "python": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "pyright"]
    }
  }
}
```

### 方法2: 直接LSPツールを使用

#### jedi-language-server
```bash
# インストール
pip install jedi-language-server

# 参照検索の例（LSPプロトコル経由）
echo '{"jsonrpc":"2.0","method":"textDocument/references","params":{...}}' | jedi-language-server
```

#### Pyright
```bash
# インストール
npm install -g pyright

# CLI使用例
pyright --dependencies  # 依存関係グラフ
pyright --stats        # コード統計
```

## 実装可能な拡張

flake.nixに以下の機能を追加可能：

```nix
# 参照検索ツール
pythonReferences = pkgs.writeShellScriptBin "python-references" ''
  FILE=$1
  SYMBOL=$2
  
  # jediを使った簡易実装
  ${pythonEnv}/bin/python -c "
import jedi
script = jedi.Script(path='$FILE')
refs = script.get_references()
for ref in refs:
    print(f'{ref.module_path}:{ref.line}:{ref.column}')
  "
'';
```

## まとめ

- **診断ツール**: エラー・警告を見つける（今回実装）
- **LSP機能**: コードナビゲーション・リファクタリング（MCPサーバー経由で利用可能）

変数の参照検索などが必要な場合は、LSMCPをMCPサーバーとして使うか、専用のLSP機能を実装する必要があります。