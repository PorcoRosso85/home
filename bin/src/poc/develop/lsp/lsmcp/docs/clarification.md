# 実装内容の整理

## 今回実装したもの

### ❌ LSP（Language Server Protocol）は使っていません

実装したのは：
1. **Jediライブラリ** - Python専用の静的解析ツール
2. **Ropeライブラリ** - Python専用のリファクタリングツール
3. **mypy + ruff** - Python専用の診断ツール

これらは**LSPではなく、Python専用のライブラリ**です。

## LSMCPが本来サポートするLSP

README記載の対応LSP：
- **pyright** - MicrosoftのPython LSP
- **pylsp** - Python LSP Server
- **rust-analyzer** - Rust用
- **gopls** - Go用
- **typescript-language-server** - TypeScript用
- など

## なぜLSPを使わなかったか

### 1. LSMCPのPython LSP問題（報告済み）
- pylspは診断でエラーを検出できない
- CLIモードはTypeScript専用
- MCPサーバーとしてしか使えない

### 2. 直接的な解決策を選択
- Python専用ツールで確実に動作
- CLIで簡単に使える
- Nix flakeで依存関係管理

## 本来のLSP使用方法

### 方法1: LSMCPをMCPサーバーとして起動
```json
{
  "mcpServers": {
    "python": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "-p", "pyright"]
    }
  }
}
```
→ Claude等のMCPクライアントから使用

### 方法2: LSPを直接使用（今回は未実装）
```bash
# pyrightを直接起動
pyright --languageserver --stdio

# LSPプロトコルでやり取り
{"jsonrpc":"2.0","method":"textDocument/references",...}
```

## まとめ

- **実装したもの**: Python専用ツールのCLIラッパー
- **実装していないもの**: LSPサーバーとの通信
- **理由**: LSMCPのPython対応が不完全なため、より実用的な方法を選択