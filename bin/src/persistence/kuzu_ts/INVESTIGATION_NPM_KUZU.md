# npm:kuzu使用調査結果

## 調査内容
`/home/nixos/bin/src/kuzu/query`と`/home/nixos/bin/src/kuzu/browse`でのnpm:kuzu使用方法を調査

## 発見事項

### 1. kuzu/query での実装
```json
// deno.json
{
  "imports": {
    "kuzu": "npm:kuzu@^0.9.0"
  },
  "nodeModulesDir": "auto"
}
```

テストコード例：
```typescript
// basicQuery.test.ts
const kuzu = await import("npm:kuzu");
const db = new kuzu.Database(":memory:");
const conn = new kuzu.Connection(db);

try {
  await conn.query("CREATE NODE TABLE User(...)");
  // 正常に動作
} finally {
  await conn.close();
  await db.close();
}
```

### 2. kuzu/browse での実装
```json
// deno.json
{
  "nodeModulesDir": "auto",
  "imports": {
    "kuzu-wasm": "npm:kuzu-wasm@^0.8.0"  // WASM版を使用
  }
}
```

## 重要な違い

### kuzu/queryアプローチ
- **動的import**を使用: `await import("npm:kuzu")`
- **明示的なクリーンアップ**: `conn.close()`, `db.close()`
- パニックが発生していない（または報告されていない）

### persistence/kuzu_tsの問題点
- **静的import**: `import { Database } from "kuzu"`
- クリーンアップが不完全
- テスト終了時にパニック発生

## 解決策

1. **動的importへの変更**
```typescript
// 現在（問題あり）
import { Database, Connection } from "kuzu";

// 改善案
const kuzu = await import("npm:kuzu");
const { Database, Connection } = kuzu;
```

2. **明示的なリソース管理**
```typescript
export async function createDatabase(path: string): Promise<DatabaseResult> {
  const kuzu = await import("npm:kuzu");
  const db = new kuzu.Database(path);
  
  // クリーンアップ関数も返す
  return {
    database: db,
    cleanup: async () => {
      await db.close();
    }
  };
}
```

3. **WASM版への移行検討**
- kuzu/browseのようにkuzu-wasmを使用
- ネイティブバインディングの問題を回避