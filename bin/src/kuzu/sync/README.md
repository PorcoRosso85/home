# @kuzu/sync

Node.js用KuzuDB同期・エクスポートユーティリティ

## 概要

KuzuDB WASMをNode.js環境で使用し、データのエクスポート機能を提供します。

## インストール

```bash
cd bin/src/kuzu/sync
pnpm install
```

## 使用方法

```typescript
import { createExportService } from './exportService.js';

const service = createExportService();

const result = await service.exportData({
  query: "MATCH (n) RETURN n",
  format: 'parquet',
  outputPath: './export.parquet'
});

if ('code' in result) {
  console.error(`Export failed: ${result.message}`);
} else {
  console.log(`Exported to: ${result.path} (${result.size} bytes)`);
}

await service.close();
```

## テスト

```bash
pnpm test
```

## 特徴

- Node.js v22+の--experimental-strip-types使用（ビルド不要）
- 最小構成でESMのみ対応
- CONVENTION.yaml準拠の関数型実装
- エラー型による明示的なエラーハンドリング