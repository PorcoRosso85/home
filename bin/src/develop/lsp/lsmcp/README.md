# lsmcp - Language Service MCP Server

## 概要

lsmcp（Language Service MCP）を簡単に実行できるシェルスクリプトです。Nix環境で必要な言語サーバーを自動的に提供し、MCPサーバーとして動作します。

## 特徴

- **インストール不要**: nix-shellで必要な依存関係を自動解決
- **高速起動**: flake評価のオーバーヘッドなし（0.1秒）
- **多言語対応**: TypeScript、Rust、Go、Python等の言語サーバーを同梱

## 背景

lsmcp（Language Service MCP）は、Model Context Protocol（MCP）サーバーとして動作し、Language Server Protocol（LSP）を通じて複数のプログラミング言語に対する高度なコード操作・解析機能を提供します。

### 主な特徴
- 🌍 多言語サポート（TypeScript/JavaScript組み込み、LSP経由で任意の言語に拡張可能）
- 🔍 セマンティックコード解析（定義へのジャンプ、参照検索、型情報）
- 🤖 AI最適化（LLM向けに設計されたライン・シンボルベースのインターフェース）

## 使い方

### 基本的な使用方法

```bash
# スクリプトを実行可能にする（初回のみ）
chmod +x lsmcp.sh

# TypeScript用MCPサーバーとして起動
./lsmcp.sh -p typescript

# Rust用MCPサーバーとして起動
./lsmcp.sh -p rust-analyzer

# ヘルプを表示
./lsmcp.sh --help
```

### リモート実行

```bash
# GitHubから直接実行
curl -sL https://raw.githubusercontent.com/user/lsmcp/main/lsmcp.sh | bash -s -- -p typescript
```

### Claude Codeとの統合

`.mcp.json`ファイルを作成して、Claude Codeから利用できます：

```json
{
  "mcpServers": {
    "typescript": {
      "command": "./lsmcp.sh",
      "args": ["-p", "typescript"]
    }
  }
}
```

## 含まれる言語サーバー

- **TypeScript/JavaScript**: typescript-language-server
- **Rust**: rust-analyzer
- **Go**: gopls
- **Python**: pyright
- **HTML/CSS/JSON**: vscode-langservers-extracted

## 技術詳細

### nix-shell shebang
このスクリプトはnix-shellのshebang機能を使用しており、実行時に必要な依存関係を自動的に解決します。初回実行時はパッケージのダウンロードに時間がかかりますが、2回目以降はキャッシュから高速に起動します。

### 動作要件
- Nix パッケージマネージャー
- インターネット接続（初回実行時）

## トラブルシューティング

### 初回実行が遅い
初回実行時は依存パッケージのダウンロードが必要です。2回目以降は高速に起動します。

### 言語サーバーが見つからない
スクリプト内で言語サーバーがバンドルされているため、別途インストールは不要です。

## 参考資料
- [lsmcp GitHub Repository](https://github.com/mizchi/lsmcp)
- [Anthropic MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)