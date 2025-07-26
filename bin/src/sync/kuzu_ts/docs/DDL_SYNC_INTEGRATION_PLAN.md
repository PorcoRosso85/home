# DDL同期統合計画

## 背景

POC `causal_with_migration`で実証済みのDDL同期機能を`sync/kuzu_ts`に統合する。

## 統合すべき主要コンポーネント

### 1. CausalOperation型の拡張

```typescript
// 現在のTemplateEvent型を拡張
interface TemplateEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  clientId: string;
  timestamp: number;
  // 追加フィールド
  dependsOn?: string[];  // 因果依存関係
  type?: 'DML' | 'DDL'; // 操作タイプ
}
```

### 2. DDLテンプレートの追加

```typescript
const DDL_TEMPLATES = {
  CREATE_NODE_TABLE: {
    type: 'DDL',
    execute: async (params) => {
      return `CREATE NODE TABLE IF NOT EXISTS ${params.tableName}(
        ${params.columns.map(c => `${c.name} ${c.type}`).join(', ')},
        PRIMARY KEY(${params.primaryKey})
      )`;
    }
  },
  ALTER_TABLE_ADD_COLUMN: {
    type: 'DDL',
    execute: async (params) => {
      return `ALTER TABLE ${params.tableName} 
        ADD ${params.ifNotExists ? 'IF NOT EXISTS' : ''} 
        ${params.columnName} ${params.columnType}
        ${params.defaultValue ? `DEFAULT ${params.defaultValue}` : ''}`;
    }
  }
  // 他のDDL操作...
};
```

### 3. ServerKuzuClientの拡張

```typescript
class ServerKuzuClient {
  // スキーマバージョン管理
  private schemaVersion: SchemaVersion = {
    version: 0,
    operations: [],
    tables: {}
  };

  async applyEvent(event: TemplateEvent): Promise<void> {
    // 依存関係チェック
    if (event.dependsOn) {
      await this.waitForDependencies(event.dependsOn);
    }

    if (event.type === 'DDL') {
      await this.applyDDLEvent(event);
    } else {
      await this.applyDMLEvent(event);
    }
  }

  private async applyDDLEvent(event: TemplateEvent): Promise<void> {
    // DDL実行とスキーマバージョン更新
    const query = DDL_TEMPLATES[event.template].execute(event.params);
    await this.conn.query(query);
    
    this.schemaVersion.version++;
    this.schemaVersion.operations.push(event.id);
    this.updateSchemaMetadata(event);
  }
}
```

### 4. 因果順序管理

```typescript
class CausalOrderManager {
  private appliedOperations = new Set<string>();
  private pendingOperations = new Map<string, TemplateEvent>();

  async processEvent(event: TemplateEvent): Promise<void> {
    if (this.canApply(event)) {
      await this.applyEvent(event);
      this.checkPendingOperations();
    } else {
      this.pendingOperations.set(event.id, event);
    }
  }

  private canApply(event: TemplateEvent): boolean {
    if (!event.dependsOn) return true;
    return event.dependsOn.every(dep => this.appliedOperations.has(dep));
  }
}
```

## 移行戦略

### Phase 1: 基本DDL同期（1週間）
- CREATE NODE TABLE
- ALTER TABLE ADD COLUMN
- 基本的な依存関係管理

### Phase 2: 高度なDDL操作（1週間）
- DROP COLUMN
- RENAME TABLE/COLUMN
- COMMENT ON TABLE

### Phase 3: スキーマバージョニング（1週間）
- スキーマ状態の永続化
- バージョン競合解決
- ロールバック機能

### Phase 4: 本番環境対応（1週間）
- エラーハンドリング強化
- パフォーマンス最適化
- 監視・ログ機能

## テスト戦略

1. **単体テスト**: 各DDL操作の正常系・異常系
2. **統合テスト**: 複数クライアント間のDDL同期
3. **ストレステスト**: 大量のDDL操作の並行実行
4. **互換性テスト**: 既存のDML操作との共存

## リスクと対策

### リスク1: 既存データとの互換性
- 対策: スキーマ移行ツールの提供

### リスク2: DDL操作の失敗
- 対策: トランザクションとロールバック機能

### リスク3: パフォーマンス劣化
- 対策: DDL操作のバッチ化とキャッシング