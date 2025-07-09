# クリーンなテスト実装ガイド

## 概要
WebSocketベースの分散システムテストにおけるリソース管理とクリーンアップの完全な実装。

## 主要コンポーネント

### 1. TestResourceManager
```typescript
export class TestResourceManager {
  private resources: TestResource[] = [];
  
  register(resource: TestResource): void
  async cleanupAll(): Promise<void>
}
```
- LIFO順序でのクリーンアップ
- 非同期クリーンアップの適切な待機
- エラーハンドリング

### 2. TestContext
```typescript
export interface TestContext {
  tempDir: string;           // 一時ディレクトリ
  wsPort: number;            // 独立したポート
  wsUrl: string;             // WebSocket URL
  serverProcess?: Deno.ChildProcess;
  resourceManager: TestResourceManager;
  clients: Map<string, any>;
}
```

### 3. withTestContext
```typescript
export async function withTestContext(
  testFn: (ctx: TestContext) => Promise<void>
): Promise<void>
```
- try-finallyによる確実なクリーンアップ
- テストごとの完全な分離

## 実装の特徴

### テストの独立性
1. **ポートの分離**: 各テストで異なるポートを使用
2. **一時ディレクトリ**: テストごとに独立したファイルシステム
3. **プロセスの分離**: 各テストで独立したWebSocketサーバー

### リソース管理
1. **自動登録**: リソース作成時に自動的にクリーンアップ登録
2. **階層的管理**: 親リソースが子リソースを管理
3. **エラー耐性**: 一部のクリーンアップが失敗しても継続

### 非同期操作の処理
1. **waitForPendingOperations**: 保留中の操作の完了待機
2. **gracefulShutdown**: 段階的なシャットダウン
3. **タイムアウト制御**: 無限待機の防止

## 使用例

```typescript
await t.step("テストケース", async () => {
  await withTestContext(async (ctx) => {
    // クライアント作成（自動クリーンアップ付き）
    const client = await createManagedTestClient(ctx, "client-id");
    
    // テスト実行
    await client.executeOperation({...});
    
    // 操作の完了待機
    await waitForPendingOperations(client);
    
    // アサーション
    assertEquals(...);
    
    // クリーンアップは自動実行
  });
});
```

## メリット

1. **リソースリークの防止**: すべてのリソースが確実に解放される
2. **テストの独立性**: 他のテストに影響を与えない
3. **デバッグの容易さ**: 問題の切り分けが簡単
4. **並列実行のサポート**: 複数テストの同時実行が可能

## ベストプラクティス

1. **早期登録**: リソース作成直後にクリーンアップを登録
2. **エラーハンドリング**: クリーンアップ中のエラーをログに記録
3. **タイムアウト設定**: 無限待機を避けるためのタイムアウト
4. **グレースフルシャットダウン**: 急な切断を避ける

## 今後の改善案

1. **リトライメカニズム**: 一時的な失敗に対する再試行
2. **メトリクス収集**: リソース使用量の監視
3. **並列度の制御**: 同時実行テスト数の制限
4. **キャッシュ機能**: 共通リソースの再利用