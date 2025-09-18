# 統合テスト実行ガイド

## 現状の分析

### 実装済み
1. **手動デモ** (`demo.html`)
   - ✅ 実際に動作確認可能
   - ✅ 視覚的に同期を確認
   - ❌ 自動化されていない

2. **単体テスト** (`test_multi_browser_sync_spec.ts`)
   - ✅ 8つの仕様をカバー
   - ✅ WebSocketクライアント/サーバーの動作確認
   - ❌ 実際のブラウザ環境ではない

3. **Playwright E2Eテスト** (`e2e/test-multi-browser-sync.spec.ts`)
   - ✅ 実際のブラウザで実行
   - ✅ WebSocket通信を監視
   - ✅ ログを検知
   - ❌ サーバー起動が手動

## 同期確認の方法

### 1. **データレベルの確認**
```typescript
// Browser2でデータが表示されるまで待機
await page2.waitForFunction(() => {
  const users = document.getElementById('users');
  return users?.textContent?.includes('Test User from Browser1');
});
```

### 2. **ログレベルの確認**
```typescript
// コンソールログを監視
page.on('console', msg => {
  console.log('[Browser]:', msg.text());
});

// ログ内容を検証
expect(logs1.some(log => log.includes('Created user'))).toBe(true);
expect(logs2.some(log => log.includes('Synced user'))).toBe(true);
```

### 3. **WebSocket通信の監視**
```typescript
page.on('websocket', ws => {
  ws.on('framesent', evt => console.log('Sent:', evt.payload));
  ws.on('framereceived', evt => console.log('Received:', evt.payload));
});
```

## 実行方法

### 手動実行（推奨）

```bash
# 1. WebSocketサーバー起動
cd /home/nixos/bin/src/poc/sync/unified_sync
nix develop . -c deno run --allow-net websocket-server.ts

# 2. HTTPサーバー起動（別ターミナル）
nix develop . -c deno run --allow-net --allow-read serve.ts

# 3. Playwrightテスト実行（別ターミナル）
nix develop . -c npx playwright test e2e/test-multi-browser-sync.spec.ts --headed
```

### 自動実行（未実装）

完全な自動化には以下が必要：

1. **playwright.config.ts の改善**
```typescript
webServer: [
  {
    command: 'deno run --allow-net websocket-server.ts',
    port: 8080,
    reuseExistingServer: false,
  },
  {
    command: 'deno run --allow-net --allow-read serve.ts',
    port: 3000,
    reuseExistingServer: false,
  }
]
```

2. **プロセス管理の改善**
- サーバーの起動/停止を確実に行う
- ポートの競合を避ける
- エラー時のクリーンアップ

## 同期の担保

### 現在担保されていること

1. **WebSocket通信**
   - ✅ イベントの送受信
   - ✅ ブロードキャスト（送信元除外）

2. **KuzuDB WASM**
   - ✅ 各ブラウザで独立したインスタンス
   - ✅ Cypherクエリによるデータ操作

3. **視覚的確認**
   - ✅ demo.htmlでリアルタイム更新
   - ✅ 作成元クライアントIDの表示

### 改善が必要な点

1. **イベント履歴**
   - 新規接続時の初期同期が未実装
   - サーバー側には履歴機能があるが、クライアント側で未使用

2. **エラーリカバリ**
   - 接続断時の再接続は実装済み
   - データ不整合時の修復機能なし

3. **パフォーマンステスト**
   - 50クライアントのテストは単体テストのみ
   - 実ブラウザでの負荷テストなし