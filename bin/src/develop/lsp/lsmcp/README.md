# lsmcp - Language Service MCP Server

## 概要

lsmcp（Language Service MCP）を簡単に実行できるシェルスクリプトです。Nix環境で必要な言語サーバーを自動的に提供し、MCPサーバーとして動作します。

## 特徴

- **完全な独立環境**: Node.jsや言語サーバーのシステムインストール不要
- **バージョン保証**: Node.js v22、各言語サーバーの動作確認済みバージョンを提供
- **高速起動**: 2回目以降は0.1秒で起動（Nixキャッシュ利用）
- **多言語対応**: TypeScript、Rust、Go、Python等の言語サーバーを自動提供

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

#### 方法1: グローバル設定（推奨）

CLIコマンドで全プロジェクトで利用可能に設定：

```bash
# このリポジトリをクローン
git clone https://github.com/user/lsmcp ~/bin/lsmcp
cd ~/bin/lsmcp
chmod +x lsmcp.sh

# Claude Codeにグローバル登録（言語別に登録可能）
claude mcp add lsmcp-ts ~/bin/lsmcp/lsmcp.sh -- -p typescript
claude mcp add lsmcp-rust ~/bin/lsmcp/lsmcp.sh -- -p rust-analyzer
claude mcp add lsmcp-go ~/bin/lsmcp/lsmcp.sh -- -p gopls
claude mcp add lsmcp-python ~/bin/lsmcp/lsmcp.sh -- -p pyright
```

登録後、Claude Codeを再起動すると、すべてのプロジェクトで利用可能になります。

#### 方法2: プロジェクト単位の設定

特定のプロジェクトでのみ使用する場合：

1. プロジェクトにスクリプトをコピー：
```bash
curl -o lsmcp.sh https://raw.githubusercontent.com/user/lsmcp/main/lsmcp.sh
chmod +x lsmcp.sh
```

2. プロジェクトルートに`.mcp.json`を作成：
```json
{
  "mcpServers": {
    "lsmcp": {
      "command": "./lsmcp.sh",
      "args": ["-p", "typescript"]
    }
  }
}
```


#### プロジェクトMCPの自動承認

すべてのプロジェクトの`.mcp.json`を自動的に信頼する場合、`~/.claude/settings.json`に追加：

```json
{
  "enableAllProjectMcpServers": true
}
```

## 含まれる言語サーバー

- **TypeScript/JavaScript**: typescript-language-server
- **Rust**: rust-analyzer
- **Go**: gopls
- **Python**: pyright
- **HTML/CSS/JSON**: vscode-langservers-extracted

## 技術詳細

### nix shell コマンド
このスクリプトはnix shellコマンドを使用しており、実行時に必要な依存関係を自動的に解決します。初回実行時はパッケージのダウンロードに時間がかかりますが、2回目以降はキャッシュから高速に起動します。

### 動作要件
- Nix パッケージマネージャー
- インターネット接続（初回実行時）

## トラブルシューティング

### 初回実行が遅い
初回実行時は依存パッケージのダウンロードが必要です。2回目以降は高速に起動します。

### 言語サーバーが見つからない
スクリプト内で言語サーバーがバンドルされているため、別途インストールは不要です。

### 既知の問題と制限事項

#### 動作確認済み
- **TypeScript/JavaScript**: 正常に動作
- **Go (gopls)**: 正常に動作
- **HTML/CSS/JSON**: 正常に動作

#### 制限事項
- **Rust (rust-analyzer)**: NixOSのパッケージビルドエラーのため、現在nix shellでの提供ができません。システムにrust-analyzerをインストールするか、rustupを使用してください。
- **Python (pyright)**: pyrightは含まれていますが、lsmcpとの通信でタイムアウトが発生する場合があります。

## 参考資料
- [lsmcp GitHub Repository](https://github.com/mizchi/lsmcp)
- [Anthropic MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)