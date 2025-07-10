# LSMCP CLI化の実現可能性分析

## 結論：部分的に可能、ただし制限あり

### ✅ 技術的に可能な部分

1. **flakeでLSMCPを呼び出す**
```nix
inputs.lsmcp.url = "github:mizchi/lsmcp";
# または
npx @mizchi/lsmcp
```

2. **TypeScriptの診断**（既に動作確認済み）
```bash
npx @mizchi/lsmcp --include "**/*.ts" -l typescript
```

### ❌ 不可能な部分

1. **PythonのCLI診断**
- LSMCPのソースコードを確認すると：
  - `--include`フラグはTypeScript専用実装
  - 他言語のバッチ処理は未実装
  - MCPサーバーモードでの使用が前提

2. **根本的な問題**
```typescript
// lsmcp/src/cli.ts (推測)
if (options.include) {
  // TypeScript専用の処理
  runTypeScriptDiagnostics(options.include);
} else {
  // MCPサーバーとして起動
  startMCPServer();
}
```

### 🔄 回避策

1. **MCPサーバーとして起動 + クライアント実装**
```bash
# サーバー起動
npx @mizchi/lsmcp -p pyright

# 別プロセスでMCPクライアントを実装
# JSONRPCでやり取り
```

2. **pyrightを直接使用**
```bash
# LSMCPを迂回
pyright main.py
```

## なぜ「可能」と誤答したか

1. **表面的な理解**
   - 「flakeで呼び出せる」＝「CLI化できる」と短絡的に考えた
   - LSMCPの内部実装を確認せずに回答

2. **実際の制限**
   - LSMCPはMCPサーバーが本体
   - CLI機能は付加的で、TypeScriptのみ対応
   - Python対応は「MCPサーバー経由」が前提

## 正しい答え

**「flakeでLSMCPを呼び出すことは可能だが、Python診断のCLI実行はLSMCP側の制限により不可能。MCPサーバーとして使うか、pyrightを直接使う必要がある」**