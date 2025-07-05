# Persistence Layer - 永続化レイヤー

イベントとスナップショットの永続化、および高速な読み込みを実現。

## 責務

### 1. イベントログ永続化
```typescript
// Append-only ログ
writeEvent(event) → position
readEvents(from, to) → Event[]
```

### 2. スナップショット管理
```typescript
// 定期的な状態保存
saveSnapshot(state, position)
loadSnapshot(position) → state
```

### 3. インデックスと検索
- 時系列インデックス
- エンティティ別イベント追跡
- 効率的な範囲クエリ

## テスト対象

- Write-Ahead Logging (WAL)
- クラッシュリカバリ
- 同時書き込みの整合性
- ストレージ効率（圧縮率）
- 読み込みレイテンシ