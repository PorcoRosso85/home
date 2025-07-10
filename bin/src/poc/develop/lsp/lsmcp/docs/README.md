# lsmcp CLI 実装状況と実証結果

リポジトリ: https://github.com/mizchi/lsmcp

## 概要

lsmcp (Language Service MCP) は、LLMがLanguage Server Protocol (LSP) 機能を使用できるようにするMCPサーバーです。
本ドキュメントは、実際のテストに基づくCLI機能の実装状況を記録したものです。

## 重要：ドキュメントと実装の乖離

lsmcpのREADMEには多くのCLI機能が記載されていますが、**実装されていない機能が多数存在**します。

### 実装状況一覧

| 機能 | ドキュメント記載 | 実装状況 | 備考 |
|------|----------------|----------|------|
| `--include` | ✅ | ✅ | TypeScript/JavaScriptのみ対応 |
| `--exclude` | ✅ | ❌ | Unknown optionエラー |
| `--project-root` | ✅ | ❌ | Unknown optionエラー |
| `--verbose` | ✅ | ❌ | Unknown optionエラー |
| 複数 `--include` | ✅ | ❌ | 単一のincludeのみ受け付け |
| 他言語でのバッチ操作 | ✅ | ❌ | TypeScript/JSのみ |

## 実際に動作するCLI機能

### 1. TypeScript/JavaScript診断

```bash
# 基本的な使い方（動作確認済み）
npx @mizchi/lsmcp --include "src/**/*.ts" -l typescript

# 実行例の出力
[lsmcp] main() called with values: {"include":"src/**/*.ts","language":"typescript"}, positionals: []
Getting diagnostics for pattern: src/**/*.ts
Found 87 files matching pattern: src/**/*.ts
Getting diagnostics...

src/common/errorHandling.test.ts:1:38 - error TS2307: Cannot find module 'vitest'...
```

### 2. パターンマッチング

```bash
# 特定ディレクトリのみ（動作確認済み）
npx @mizchi/lsmcp --include "src/lsp/*.ts" -l typescript

# 単一ファイル指定も可能
npx @mizchi/lsmcp --include "src/index.ts" -l typescript
```

### 3. その他の動作確認済みコマンド

```bash
# ヘルプ表示
npx @mizchi/lsmcp --help

# 言語一覧（ただし実際はTypeScript/JSのみがCLIで使用可能）
npx @mizchi/lsmcp --list
```

## エラーが出る場合の対処

### 1. "Unknown option" エラー

```bash
# これらはドキュメントには記載されているが未実装
npx @mizchi/lsmcp --exclude "node_modules/**"  # ❌ エラー
npx @mizchi/lsmcp --project-root /path/to/project  # ❌ エラー
npx @mizchi/lsmcp --verbose  # ❌ エラー
```

**対処法**: これらのオプションは使用できません。`--include`のみを使用してください。

### 2. "lsmcp: command not found" エラー

bashのaliasやシェル関数として`lsmcp`が定義されていても、npx実行時には使用できません。
必ず`npx @mizchi/lsmcp`の形式で実行してください。

### 3. 他言語での診断

```bash
# これは動作しない（エラーは出ないが診断結果も出ない）
npx @mizchi/lsmcp --include "**/*.rs" --bin rust-analyzer
```

**理由**: `--include`によるバッチ診断はTypeScript/JavaScript専用の実装です。

## アーキテクチャ理解のポイント

### MCP層とLSP層の分離

```
/src/
├── mcp/        # MCPサーバー実装（ラッパー層）
├── lsp/        # 純粋なLSP機能
│   ├── lspClient.ts    # LSPクライアント実装
│   └── tools/          # 各種LSPツール
└── ts/         # TypeScript特化機能
```

### CLI実行時の動作

1. `--include`が指定された場合のみCLIモードで動作
2. ファイルパターンにマッチするファイルを収集
3. TypeScriptコンパイラAPIで診断を実行
4. 結果を表示して終了（MCPサーバーは起動しない）

## 本来の使用方法

lsmcpは本来MCPサーバーとして使用することを想定しています：

```json
// .mcp.json での設定例
{
  "mcpServers": {
    "lsmcp": {
      "command": "npx",
      "args": ["-y", "@mizchi/lsmcp", "--language", "typescript"]
    }
  }
}
```

MCPクライアント（Claude等）から接続して、以下のようなツールを使用：
- `lsmcp_rename_symbol`
- `lsmcp_move_file`
- `lsmcp_get_diagnostics`
- など

## まとめ

- CLI単体使用は**TypeScript/JavaScriptの診断機能のみ**実用的
- ドキュメントの多くの機能は**願望**であり未実装
- 本質的には**MCPサーバー**として設計されている
- LSP機能を直接使いたい場合は、各言語のLSPサーバーを直接使用する方が確実

## 参考：直接LSPサーバーを使用する例

```bash
# TypeScript (tsserver)
echo '{"seq":1,"type":"request","command":"open","arguments":{"file":"test.ts"}}' | tsserver

# rust-analyzer
echo '{"jsonrpc":"2.0","id":1,"method":"textDocument/hover","params":{}}' | rust-analyzer
```