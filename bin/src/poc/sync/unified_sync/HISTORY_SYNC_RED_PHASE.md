# 履歴同期 TDD Red Phase 仕様

## 概要

新規接続したブラウザが、過去に作成されたデータを自動的に取得する機能の仕様定義。

## 現在の問題

```
時刻 10:00: Browser1がユーザーAliceを作成
時刻 10:01: Browser2が新規接続 → Aliceが見えない ❌
時刻 10:02: Browser1がユーザーBobを作成 → Browser2でBobは見える ✅
```

## 必要な仕様

### 1. 新規接続時の自動履歴取得

```typescript
// 期待される動作
const client = await connectToServer("newClient");
// 接続時に自動的に履歴を要求
// → 過去の全イベントを受信
```

### 2. 部分的な履歴取得（位置指定）

```typescript
// 特定位置からの履歴取得
const history = await client.requestHistoryFrom(position);
// position以降のイベントのみ取得
```

### 3. 履歴取得後のリアルタイム同期継続

- 履歴取得完了後も通常のリアルタイム同期が動作
- 履歴イベントとリアルタイムイベントの区別

### 4. 重複イベントの防止

- 既にリアルタイムで受信したイベントを履歴で重複受信しない
- イベントIDによる重複チェック

### 5. 大量履歴のページング

```typescript
// ページング対応
const page = await client.requestHistoryPage({
  fromPosition: 0,
  limit: 100
});
```

### 6. 接続エラー時の履歴再取得

- 履歴取得中の切断に対応
- 再接続時に続きから取得

### 7. 履歴の整合性チェック

- チェックサムによる検証
- 改ざん検出

### 8. 履歴圧縮・最適化

- 同一エンティティへの複数更新を圧縮
- 最終状態のみ送信してトラフィック削減

## テストファイル

### 単体テスト
- `test_history_sync_spec.ts` - 8つの仕様をカバー

### E2Eテスト
- `e2e/test-history-sync.spec.ts` - 実ブラウザでの動作確認

## 実装に必要な変更

### サーバー側（一部実装済み）
```typescript
case "requestHistory":
  const history = getEventHistory(fromPosition);
  socket.send(JSON.stringify({ type: "history", events: history }));
```

### クライアント側（未実装）
```typescript
// demo.html の initialize() に追加
async initialize() {
  // ... 既存の初期化処理 ...
  
  // 履歴を要求
  const history = await this.requestHistory();
  await this.applyHistoryEvents(history);
  
  // その後リアルタイム同期開始
  this.startRealtimeSync();
}
```

## 期待される効果

1. **完全な同期**: 新規ブラウザも全データを持つ
2. **一貫性**: 全ブラウザで同じデータ
3. **効率性**: 必要な部分のみ取得
4. **信頼性**: エラー時の再取得

## 次のステップ

1. このRed Phaseテストを実行して失敗を確認
2. Green Phaseで実装
3. Refactoringで最適化