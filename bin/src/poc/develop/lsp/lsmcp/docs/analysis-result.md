# LSMCP実装分析結果

## 結論
**サーバー実行なしでのCLI実行は現在の実装では困難**

## 分析詳細

### 1. アーキテクチャ
- LSMCPは完全にMCPサーバーとして設計されている
- エントリーポイント: `src/mcp/lsmcp.ts`
- 実行フロー:
  1. コマンドライン引数を解析
  2. LSPサーバープロセスを起動
  3. MCPサーバーを起動
  4. クライアントからの要求を待機

### 2. --includeオプションについて
- オプション定義は存在する（line 68-72）
- しかし、特別な処理は実装されていない
- コメント（line 223-224）によると「lsp_get_all_diagnosticsツールに渡される」とあるが、実際の処理は見当たらない

### 3. TypeScript診断の特別処理
- 期待されていた`runTypeScriptDiagnostics`のような関数は存在しない
- TypeScript専用ツール（`src/ts/tools/`）はあるが、診断用ではない
- すべての言語は同じMCPサーバー経由で処理される

### 4. LSPツールの実装
LSPツールは`src/lsp/tools/`に実装されているが、すべてMCPツールとして登録される：
- `lspFindReferences.ts` - 参照検索
- `lspRenameSymbol.ts` - シンボルリネーム
- `lspGetDiagnostics.ts` - 診断取得
- `lspGetAllDiagnostics.ts` - 全ファイル診断

これらはMCPサーバー経由でのみアクセス可能。

## CLI実行を実現するための方法

### 1. 現実的なアプローチ: MCPクライアントの実装
```bash
# MCPサーバーを起動
npx @mizchi/lsmcp -p pyright &

# 別プロセスでMCPクライアントから要求
mcp-client call lsmcp_find_references --params '{...}'
```

### 2. Nix Flakeでのラッパー実装
- MCPサーバーを内部で起動
- stdio経由でJSON-RPC通信
- 結果を整形してCLI出力

### 3. 直接的なLSP通信
- LSMCPを介さず、pyrightなどのLSPサーバーと直接通信
- より複雑だが、完全な制御が可能

## 推奨される次のステップ

1. **短期的**: pyrightを直接使用する簡易CLIツール
2. **中期的**: MCPクライアントを含むNix Flakeラッパー
3. **長期的**: LSMCPへのCLIモード追加（PR）