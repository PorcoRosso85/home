# 現在のDDL同期状況

## 実装状況サマリー

### ✅ POCで実証済み（causal_with_migration）
- 因果順序ベースのDDL同期
- CREATE TABLE, ALTER TABLE等の基本操作
- 依存関係管理（dependsOn）
- スキーマバージョニング

### ❌ 本プロジェクト（sync/kuzu_ts）未実装
- DDL操作のイベント化
- 動的スキーマ変更
- DDL同期メカニズム
- スキーマバージョン管理

### 🚧 現在の制限事項

1. **固定スキーマ方式**
```typescript
// 各クライアントが起動時に同じスキーマを作成
private async createSchema(): Promise<void> {
  await this.conn.query(`CREATE NODE TABLE IF NOT EXISTS User(...)`);
  await this.conn.query(`CREATE NODE TABLE IF NOT EXISTS Post(...)`);
  // 固定のテーブル定義
}
```

2. **DDLイベントなし**
- DML操作（CREATE, UPDATE等）のみがイベントとして扱われる
- DDL操作はイベントストリームに含まれない

3. **スキーマ不整合リスク**
- 新しいテーブルやカラムを追加する場合、全インスタンスの再起動が必要
- 動的なスキーマ進化に対応できない

## 統合に必要な作業

### 1. イベントタイプの拡張
```typescript
interface TemplateEvent {
  // 既存フィールド
  type?: 'DML' | 'DDL'; // 追加
  dependsOn?: string[];  // 追加
}
```

### 2. DDLテンプレートの追加
```typescript
const templates = {
  // 既存のDMLテンプレート
  CREATE_USER: { type: 'DML', ... },
  
  // 新規DDLテンプレート
  CREATE_TABLE: { type: 'DDL', ... },
  ALTER_TABLE_ADD_COLUMN: { type: 'DDL', ... }
};
```

### 3. イベント処理の拡張
```typescript
async applyEvent(event: TemplateEvent) {
  if (event.type === 'DDL') {
    await this.applyDDLEvent(event);
  } else {
    await this.applyDMLEvent(event);
  }
}
```

## 移行パス

### Option 1: 段階的統合（推奨）
1. まずCREATE TABLEのみ実装
2. 動作確認後、ALTER操作を追加
3. 最後に複雑なDDL操作を実装

### Option 2: 完全統合
1. POCのコードをそのまま移植
2. 既存システムとの統合テスト
3. 本番環境への適用

## テスト戦略

現在のテストはすべてignore状態：
- `tests/ddl_sync.test.ts` - DDL同期の基本テスト
- `tests/oltp_features_skip.test.ts` - ALTER操作のテスト

これらを有効化するには実装が必要。