# DDL同期設計

## 現状の課題

現在のsync/kuzu_tsはDML（データ操作）のみを同期し、DDL（スキーマ定義）は同期されません：

- 各インスタンスは起動時に固定スキーマを作成
- スキーマ変更は手動で全インスタンスに適用が必要
- 動的なスキーマ進化に対応できない

## DDL同期の実装案

### 1. DDLイベントテンプレート追加

```typescript
const DDL_TEMPLATES = {
  CREATE_NODE_TABLE: {
    query: (params) => `
      CREATE NODE TABLE IF NOT EXISTS ${params.tableName}(
        ${params.columns.map(col => `${col.name} ${col.type}`).join(', ')},
        PRIMARY KEY(${params.primaryKey})
      )
    `
  },
  CREATE_REL_TABLE: {
    query: (params) => `
      CREATE REL TABLE IF NOT EXISTS ${params.tableName}(
        FROM ${params.fromTable} TO ${params.toTable}
        ${params.properties ? ', ' + params.properties : ''}
      )
    `
  },
  ALTER_TABLE_ADD_COLUMN: {
    query: (params) => `
      ALTER TABLE ${params.tableName} 
      ADD COLUMN ${params.columnName} ${params.columnType}
    `
  },
  DROP_TABLE: {
    query: (params) => `
      DROP TABLE IF EXISTS ${params.tableName}
    `
  }
};
```

### 2. スキーマバージョン管理

```typescript
interface SchemaVersion {
  version: number;
  appliedAt: number;
  ddlEvents: TemplateEvent[];
}

class SchemaManager {
  private currentVersion: number = 0;
  private appliedDDLs: Map<string, SchemaVersion> = new Map();

  async applyDDLEvent(event: TemplateEvent): Promise<void> {
    // DDLイベントの適用とバージョン管理
    if (event.template.startsWith('DDL_')) {
      // 冪等性の確保
      if (this.appliedDDLs.has(event.id)) {
        return;
      }
      
      // DDL実行
      await this.executeDDL(event);
      
      // バージョン記録
      this.currentVersion++;
      this.appliedDDLs.set(event.id, {
        version: this.currentVersion,
        appliedAt: Date.now(),
        ddlEvents: [event]
      });
    }
  }
}
```

### 3. 初期化時のスキーマ同期

```typescript
async initializeWithSchemaSync(): Promise<void> {
  // 1. 最新のスキーマバージョンを取得
  const latestSchema = await this.fetchLatestSchema();
  
  // 2. DDLイベントを時系列順に適用
  for (const ddlEvent of latestSchema.ddlEvents) {
    await this.applyDDLEvent(ddlEvent);
  }
  
  // 3. データイベントの適用
  await this.replayDataEvents();
}
```

### 4. 実装の課題と考慮事項

#### 冪等性の確保
- CREATE TABLE IF NOT EXISTS の使用
- ALTER操作の前に現在の状態を確認
- エラー処理と再試行メカニズム

#### 互換性の管理
- 後方互換性のないスキーマ変更の検出
- ローリングアップデート時の一時的な不整合への対処
- スキーママイグレーション戦略

#### パフォーマンス
- DDL操作はDMLより重い
- スキーマ変更中のダウンタイム最小化
- インデックス作成の非同期化

## 実装優先度

1. **Phase 1**: CREATE TABLE系の基本DDL同期
2. **Phase 2**: ALTER TABLE によるカラム追加
3. **Phase 3**: インデックス管理
4. **Phase 4**: 複雑なスキーマ変更（カラム削除、型変更等）

## セキュリティ考慮事項

- DDL実行権限の制限
- SQLインジェクション対策（パラメータ化クエリ）
- スキーマ変更の監査ログ