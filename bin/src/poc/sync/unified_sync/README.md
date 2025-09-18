# Unified Sync - KuzuDB WASM + WebSocket + Event Sourcing

## 概要
ブラウザ間でKuzuDBの状態を同期するための統合実装。

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐
│   Browser A     │     │   Browser B     │
│                 │     │                 │
│ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │KuzuDB WASM  │ │     │ │KuzuDB WASM  │ │
│ └─────────────┘ │     │ └─────────────┘ │
│        ↓        │     │        ↓        │
│ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │Template Exec│ │     │ │Template Exec│ │
│ └─────────────┘ │     │ └─────────────┘ │
│        ↓        │     │        ↓        │
│ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │  WebSocket  │ │     │ │  WebSocket  │ │
│ └──────┬──────┘ │     │ └──────┬──────┘ │
└────────┼────────┘     └────────┼────────┘
         │                       │
         └───────────┬───────────┘
                     ↓
            ┌────────────────┐
            │  Event Store   │
            │   (Server)     │
            └────────────────┘
```

## KuzuDB WASM使用方法（bin/docs規約準拠）

### ブラウザ環境
```typescript
// デフォルトビルド（推奨）
import { BrowserKuzuClientImpl } from "./browser_kuzu_client.ts";

const client = new BrowserKuzuClientImpl();
await client.initialize();
```

### Worker設定（必要な場合）
```typescript
class CustomBrowserKuzuClient extends BrowserKuzuClientImpl {
  private getWorkerPath(): string {
    return '/assets/kuzu-worker.js';
  }
}
```

## テンプレートベースの同期

### セキュリティ
- Cypherインジェクション対策実装済み
- テンプレート方式で安全なクエリ実行

### サポートされるテンプレート
- `CREATE_USER`: ユーザー作成
- `UPDATE_USER`: ユーザー更新
- `CREATE_POST`: 投稿作成
- `FOLLOW_USER`: フォロー関係作成

## テスト実行

```bash
# 統合テスト実行
nix develop -c deno test --allow-all test_browser_kuzu_websocket_integration.ts
```

## 実装状況
- ✅ TDD Red フェーズ完了
- ✅ TDD Green フェーズ完了
- ⏳ E2E ネットワーク検証（次のステップ）