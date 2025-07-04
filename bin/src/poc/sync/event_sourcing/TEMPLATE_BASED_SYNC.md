# Template-Based Sync POC

## アーキテクチャ

```
Browser A                    Server                      Browser B
[KuzuDB WASM]               [Template Registry]          [KuzuDB WASM]
[Templates]                 [Event Store]               [Templates]
     ↓                           ↓                           ↓
1. テンプレート実行        2. イベント保存・配信      3. テンプレート実行
   {template: "CREATE_USER",    
    params: {...}}
```

## 実装方針

### 1. Template Registry（共有）
```typescript
// templates/index.ts
export const TEMPLATES = {
  CREATE_USER: await loadTemplate('create_user.cypher'),
  UPDATE_USER: await loadTemplate('update_user.cypher'),
  FOLLOW_USER: await loadTemplate('follow_user.cypher'),
  CREATE_POST: await loadTemplate('create_post.cypher'),
  DELETE_OLD_POSTS: await loadTemplate('delete_old_posts.cypher')
};

// 各テンプレートのメタデータ
export const TEMPLATE_METADATA = {
  CREATE_USER: {
    requiredParams: ['id', 'name', 'email', 'createdAt'],
    impact: 'CREATE_NODE',
    validation: {
      id: 'string',
      name: 'string',
      email: 'email',
      createdAt: 'datetime'
    }
  }
  // ...
};
```

### 2. Client Implementation
```typescript
class TemplateBasedSyncClient {
  async executeTemplate(templateName: string, params: Record<string, any>) {
    // 1. ローカルで実行
    const query = TEMPLATES[templateName];
    const result = await this.kuzu.query(query, params);
    
    // 2. サーバーに送信（テンプレート名とパラメータのみ）
    await this.sendToServer({
      type: 'TEMPLATE_EXECUTION',
      template: templateName,
      params: params,
      timestamp: Date.now()
    });
    
    return result;
  }
}
```

### 3. Server Implementation
```typescript
class TemplateEventStore {
  handleTemplateExecution(event: TemplateEvent) {
    // 1. バリデーション
    const metadata = TEMPLATE_METADATA[event.template];
    this.validateParams(event.params, metadata);
    
    // 2. イベント保存
    const storedEvent = {
      id: generateId(),
      ...event,
      checksum: this.calculateChecksum(event)
    };
    
    this.events.push(storedEvent);
    
    // 3. 他のクライアントに配信
    this.broadcast(storedEvent);
  }
}
```

## テスト計画

1. **基本的なテンプレート実行**
   - 各テンプレートの実行と同期
   - パラメータバリデーション

2. **セキュリティ**
   - 存在しないテンプレートの拒否
   - パラメータインジェクション対策
   - 必須パラメータチェック

3. **同期の整合性**
   - 複数クライアントでの実行順序
   - 競合するテンプレート実行

4. **パフォーマンス**
   - テンプレートのキャッシュ
   - バッチ実行

## 利点

1. **セキュリティ**: Cypherインジェクション完全防止
2. **予測可能性**: 実行前に影響を把握
3. **監査性**: テンプレート名で操作を追跡
4. **保守性**: テンプレートの一元管理

## 制限事項

1. アドホッククエリは実行不可
2. テンプレートの事前定義が必要
3. 複雑な動的クエリには不向き