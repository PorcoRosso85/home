# ⚠️ WARNING: KuzuDB ESM対応状況

## KuzuDB公式ドキュメントより

> **Node.js**: This build is optimized for Node.js and uses Node.js's filesystem instead of Emscripten's default filesystem (NODEFS flag is enabled). This build also supports multi-threading. **It is distributed as a CommonJS module rather than an ES module to maximize compatibility**. This build is located in the nodejs directory. Note that this build only works in Node.js and does not work in the browser environment.

## 現状

| ビルド | ESM対応 | 使用方法 |
|--------|---------|----------|
| Browser (default) | ✅ 対応 | `import kuzu from "kuzu-wasm"` |
| Browser (multithreaded) | ✅ 対応 | `import kuzu from "kuzu-wasm/multithreaded"` |
| Node.js | ❌ 非対応 | `require("kuzu-wasm/nodejs")` のみ |

## 解決策

### CTSファイルによるブリッジ

```typescript
// kuzu_storage.cts (CommonJS)
const kuzu = require("kuzu-wasm/nodejs");
module.exports = { KuzuNodeStorage };

// kuzu_storage_factory.ts (ESM)
const { KuzuNodeStorage } = await import("./kuzu_storage.cjs");
```

### ファイル構成

- `*.ts` - ESモジュール（デフォルト）
- `*.cts` - CommonJSモジュール（KuzuDB Node.js用）
- `*.mts` - ESモジュール（明示的）

## 制約事項

1. **Node.js環境**: KuzuDB Node.js版はCommonJSのみ
2. **型定義**: CTSファイルでは型定義が制限される
3. **動的インポート**: ESMからCTSは動的インポートのみ

## 将来的な改善

KuzuDBプロジェクトにESMサポートのリクエストを検討：
- https://github.com/kuzudb/kuzu/issues

現時点では、CTSブリッジが最も現実的な解決策です。