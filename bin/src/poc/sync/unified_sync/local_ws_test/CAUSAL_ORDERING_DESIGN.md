# 因果順序ベースの同期設計

## 概要
文字列編集の「IDベース挿入」アプローチをDB操作に適用

## データ構造

```typescript
interface CausalOperation {
  id: string;                    // 操作の一意ID
  dependsOn: string[];          // 依存する操作のID配列
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'INCREMENT';
  payload: {
    cypherQuery?: string;
    nodeId?: string;
    property?: string;
    delta?: number;
  };
  clientId: string;
  timestamp: number;
  applied: boolean;             // サーバーで適用済みか
}

// 例：Aliceを作成してから年齢を更新
const op1: CausalOperation = {
  id: 'op-001',
  dependsOn: [],              // 依存なし
  type: 'CREATE',
  payload: { cypherQuery: "CREATE (n:User {id: 'alice', age: 30})" }
};

const op2: CausalOperation = {
  id: 'op-002', 
  dependsOn: ['op-001'],      // op1の後に実行
  type: 'INCREMENT',
  payload: { nodeId: 'alice', property: 'age', delta: 1 }
};
```

## 競合解決

### 1. インクリメント操作
```typescript
// 5つの並行インクリメント
op1: { type: 'INCREMENT', delta: 1, dependsOn: ['create-alice'] }
op2: { type: 'INCREMENT', delta: 1, dependsOn: ['create-alice'] }
op3: { type: 'INCREMENT', delta: 1, dependsOn: ['create-alice'] }
op4: { type: 'INCREMENT', delta: 1, dependsOn: ['create-alice'] }
op5: { type: 'INCREMENT', delta: 1, dependsOn: ['create-alice'] }

// サーバーですべて累積: age = 30 + 1 + 1 + 1 + 1 + 1 = 35
```

### 2. 同じプロパティへの SET 操作
```typescript
// タイムスタンプでLast-Write-Wins
op1: { type: 'UPDATE', set: { age: 31 }, timestamp: 1000 }
op2: { type: 'UPDATE', set: { age: 32 }, timestamp: 1001 } // 勝利
```

### 3. 削除と更新の競合
```typescript
op1: { type: 'DELETE', nodeId: 'alice' }
op2: { type: 'UPDATE', nodeId: 'alice', dependsOn: ['some-other-op'] }

// サーバーで解決: 削除が先なら更新は無視
```

## 実装例

```typescript
class CausalOperationStore {
  private operations: Map<string, CausalOperation> = new Map();
  private applied: Set<string> = new Set();
  
  async applyOperation(op: CausalOperation) {
    // 依存関係をチェック
    for (const depId of op.dependsOn) {
      if (!this.applied.has(depId)) {
        // 依存する操作がまだ適用されていない
        this.operations.set(op.id, op);
        return; // 後で再試行
      }
    }
    
    // 操作を適用
    switch (op.type) {
      case 'INCREMENT':
        await this.applyIncrement(op);
        break;
      case 'CREATE':
        await this.applyCreate(op);
        break;
      // ...
    }
    
    this.applied.add(op.id);
    
    // この操作に依存している操作を再チェック
    this.checkPendingOperations();
  }
  
  private checkPendingOperations() {
    for (const [id, op] of this.operations) {
      if (!this.applied.has(id)) {
        this.applyOperation(op); // 再試行
      }
    }
  }
}
```

## 利点

1. **シンプルな実装**
   - CRDTの複雑なアルゴリズムが不要
   - 因果関係を明示的に管理

2. **柔軟な競合解決**
   - サーバー側でカスタムロジックを実装可能
   - ビジネスルールに応じた解決

3. **デバッグが容易**
   - 操作の依存関係が明確
   - 実行順序を追跡可能

## 注意点

1. **メモリ使用量**
   - すべての操作IDを保持する必要がある
   - 定期的なガベージコレクションが必要

2. **遅延の可能性**
   - 依存する操作を待つ必要がある
   - ネットワーク分断時の考慮

3. **循環依存の防止**
   - 操作グラフが DAG であることを保証