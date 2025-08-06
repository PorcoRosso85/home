# lsmcp Flake Purpose and Requirements

## 目的

このflakeは以下の2つの主要な目的を持ちます：

1. **リポジトリのためのflake.nixを提供**
   - lsmcpリポジトリ用の標準的なNix flake設定
   - 開発環境の提供
   - パッケージビルドの定義

2. **MCP設定をファイルに書き込む機能**
   - `.mcp.json`ファイルへの設定書き込み
   - Claude CLIとの統合設定
   - 言語サーバーの自動設定

## 背景

lsmcp（Language Service MCP）は、Model Context Protocol（MCP）サーバーとして動作し、Language Server Protocol（LSP）を通じて複数のプログラミング言語に対する高度なコード操作・解析機能を提供します。

### 主な特徴
- 🌍 多言語サポート（TypeScript/JavaScript組み込み、LSP経由で任意の言語に拡張可能）
- 🔍 セマンティックコード解析（定義へのジャンプ、参照検索、型情報）
- 🤖 AI最適化（LLM向けに設計されたライン・シンボルベースのインターフェース）

## Flake設計要件

### 1. 開発環境
- Node.js環境（lsmcpの実行に必要）
- 各言語のLSPサーバー（オプション）
  - TypeScript: typescript-language-server
  - Rust: rust-analyzer
  - Python: pyright
  - Go: gopls
  - その他

### 2. MCP設定生成機能
`.mcp.json`の自動生成・更新機能：

```json
{
  "mcpServers": {
    "typescript": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "typescript"]
    },
    "rust": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "rust-analyzer"]
    }
  }
}
```

### 3. 提供すべき機能
- `nix develop`: 開発環境の起動
- `nix run .#setup-mcp`: MCP設定ファイルの生成
- `nix run .#lsmcp`: lsmcpの直接実行
- `nix build`: パッケージのビルド（必要に応じて）

## 実装方針

1. **基本的なflake構造**
   - inputs: nixpkgs, flake-utils
   - outputs: devShells, packages, apps

2. **MCP設定スクリプト**
   - 設定ファイルの存在確認
   - 既存設定とのマージ
   - バックアップの作成
   - 設定の検証

3. **言語別の設定プリセット**
   - 各言語用の推奨設定
   - カスタム設定のサポート
   - 環境変数による設定

## 使用例

```bash
# 開発環境に入る
nix develop

# MCP設定を生成（TypeScriptとRust用）
nix run .#setup-mcp -- --languages typescript,rust

# カスタム設定で生成
nix run .#setup-mcp -- --config custom-config.json

# lsmcpを直接実行
nix run .#lsmcp -- -p typescript
```

## 参考資料
- [lsmcp GitHub Repository](https://github.com/mizchi/lsmcp)
- [Anthropic MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)