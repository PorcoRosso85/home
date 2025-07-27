# テスト統合計画

## 1. DDL同期テストの統合

### 現状
- `ddl_sync.test.ts` - 基本機能（15テスト）
- `ddl_sync_integration.test.ts` - 統合テスト（8テスト）
- `ddl_sync_e2e.test.ts` - E2Eテスト（5テスト）

### 統合後：`ddl_sync_complete.test.ts`
```typescript
describe("DDL Sync Complete Test Suite", () => {
  describe("Unit Tests", () => {
    // ddl_sync.test.tsの内容
  });
  
  describe("Integration Tests", () => {
    // ddl_sync_integration.test.tsの内容
  });
  
  describe("E2E Tests", () => {
    // ddl_sync_e2e.test.tsの内容
  });
});
```

## 2. アーカイブテストの統合

### 現状
- `archive_policy.test.ts` - ポリシー判定（5テスト）
- `archive_executor.test.ts` - 実行ロジック（7テスト）
- `archivable_events.test.ts` - イベント判定（4テスト）
- `unified_event_store_archive.test.ts` - 統合動作（6テスト）

### 統合後：`archive_complete.test.ts`
```typescript
describe("Archive Complete Test Suite", () => {
  describe("Policy Tests", () => {
    // archive_policy.test.tsの内容
  });
  
  describe("Execution Tests", () => {
    // archive_executor.test.tsの内容
  });
  
  describe("Event Selection Tests", () => {
    // archivable_events.test.tsの内容
  });
  
  describe("Integration Tests", () => {
    // unified_event_store_archive.test.tsの内容
  });
});
```

## 3. 実施タイミング

現時点では以下の理由により、統合は将来のタスクとして計画：

1. **動作中のシステムへの影響を最小化**
   - 現在サーバーが稼働中
   - テストの統合は慎重に行う必要がある

2. **段階的な実施**
   - まず1つのグループ（例：アーカイブ）から開始
   - 成功したら他のグループへ展開

3. **CI/CDパイプラインの確認**
   - 統合前にテスト実行時間を測定
   - 統合後のパフォーマンスを比較