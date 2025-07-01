# KuzuDB vs RDB - ロールベース認可の比較

## 基本的なRBAC: KuzuDBが簡単 ⭐⭐⭐⭐⭐

### RDBの場合
```sql
-- 5つ以上のテーブルが必要
CREATE TABLE users (id, name);
CREATE TABLE roles (id, name);
CREATE TABLE permissions (id, resource, action);
CREATE TABLE user_roles (user_id, role_id);
CREATE TABLE role_permissions (role_id, permission_id);

-- 権限チェックが複雑
SELECT COUNT(*) FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.id = ? AND p.resource = ? AND p.action = ?;
```

### KuzuDBの場合
```cypher
-- 直感的な1クエリ
MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(:Role)-[:CAN_PERFORM]->
      (p:Permission {resource: $resource, action: $action})
RETURN COUNT(p) > 0
```

## 複雑なRBACシナリオ: KuzuDBが圧倒的に簡単

### 1. 階層ロール継承
**シナリオ**: 管理者は一般ユーザーの権限も持つ

**RDB**: 
```sql
-- 再帰CTEが必要で複雑
WITH RECURSIVE role_hierarchy AS (
    SELECT id, parent_id FROM roles WHERE id = ?
    UNION ALL
    SELECT r.id, r.parent_id FROM roles r
    JOIN role_hierarchy rh ON r.id = rh.parent_id
)
-- さらに権限チェックのJOINが必要
```

**KuzuDB**:
```cypher
-- 階層を自然に表現
MATCH (u:User)-[:HAS_ROLE]->(:Role)-[:INHERITS*0..]->(r:Role)
      -[:CAN_PERFORM]->(p:Permission)
WHERE u.id = $user_id AND p.resource = $resource
RETURN COUNT(p) > 0
```

### 2. 条件付き権限
**シナリオ**: 部門内のリソースのみアクセス可能

**RDB**:
```sql
-- 複雑な条件結合
SELECT * FROM resources r
JOIN user_departments ud ON r.department_id = ud.department_id
JOIN user_roles ur ON ud.user_id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
WHERE ud.user_id = ? AND rp.permission = 'read'
```

**KuzuDB**:
```cypher
-- 関係性が明確
MATCH (u:User {id: $user_id})-[:BELONGS_TO]->(d:Department)
      <-[:BELONGS_TO]-(r:Resource)
WHERE EXISTS((u)-[:HAS_ROLE]->(:Role {name: 'reader'}))
RETURN r
```

### 3. 動的権限（時限、委任）
**シナリオ**: 期間限定の権限、権限の委任

**RDB**:
```sql
-- 時限権限は複雑なテーブル設計が必要
CREATE TABLE temporary_permissions (
    id, user_id, permission_id, 
    valid_from, valid_until, delegated_by
);
-- チェック時に日付条件も追加
```

**KuzuDB**:
```cypher
// 関係に属性を持たせるだけ
MATCH (u:User)-[r:HAS_PERMISSION {
    valid_from: $from,
    valid_until: $until,
    delegated_by: $delegator
}]->(p:Permission)
WHERE u.id = $user_id 
  AND datetime() >= r.valid_from 
  AND datetime() <= r.valid_until
RETURN p
```

### 4. コンテキスト認可
**シナリオ**: プロジェクトメンバーのみ、作成者のみ編集可

**RDB**:
```sql
-- 多数のテーブル結合
SELECT * FROM requirements r
LEFT JOIN project_members pm ON r.project_id = pm.project_id
WHERE (r.created_by = ? OR pm.user_id = ?)
  AND EXISTS (
    SELECT 1 FROM user_roles ur
    JOIN role_permissions rp ON ur.role_id = rp.role_id
    WHERE ur.user_id = ? AND rp.action = 'edit'
  )
```

**KuzuDB**:
```cypher
// パスの探索が簡単
MATCH (u:User {id: $user_id})
MATCH (req:Requirement {id: $req_id})
WHERE (req)-[:CREATED_BY]->(u)
   OR EXISTS((u)-[:MEMBER_OF]->(:Project)<-[:BELONGS_TO]-(req))
   AND EXISTS((u)-[:HAS_ROLE]->(:Role)-[:CAN_PERFORM]->(:Permission {action: 'edit'}))
RETURN req
```

## 特に優れている点

### 1. 権限の可視化
```cypher
// ユーザーの全権限を可視化
MATCH path = (u:User {id: $user_id})-[:HAS_ROLE|:BELONGS_TO|:CAN_PERFORM*1..5]->()
RETURN path
```

### 2. 権限の推論
```cypher
// なぜこのユーザーがアクセスできるか
MATCH path = (u:User {id: $user_id})-[*1..5]->(r:Resource {id: $resource_id})
WHERE ALL(rel IN relationships(path) WHERE type(rel) IN ['HAS_ROLE', 'CAN_ACCESS', 'OWNS'])
RETURN path
```

### 3. 異常検知
```cypher
// 循環する権限継承を検出
MATCH (r:Role)-[:INHERITS*1..]->(r)
RETURN r
```

## 実装例: 複合的な認可

```python
class AdvancedRBAC:
    """高度なロールベース認可"""
    
    def check_access(self, user_id: str, resource_id: str, action: str) -> bool:
        """複合的なアクセスチェック"""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (res:Resource {id: $resource_id})
        
        // 複数の認可パスをチェック
        RETURN 
            // 1. 直接の所有者
            EXISTS((res)-[:OWNED_BY]->(u))
            OR
            // 2. ロールベース権限
            EXISTS((u)-[:HAS_ROLE]->(:Role)-[:CAN_PERFORM]->
                   (:Permission {resource_type: res.type, action: $action}))
            OR
            // 3. プロジェクトメンバー
            EXISTS((u)-[:MEMBER_OF]->(:Project)<-[:BELONGS_TO]-(res))
            AND EXISTS((u)-[:HAS_ROLE]->(:Role {name: 'project_member'}))
            OR
            // 4. 部門権限
            EXISTS((u)-[:BELONGS_TO]->(:Department)<-[:MANAGED_BY]-(res))
            AND EXISTS((u)-[:HAS_ROLE]->(:Role)-[:CAN_MANAGE_DEPT_RESOURCES]->())
            OR
            // 5. 委任された権限
            EXISTS((u)<-[:DELEGATED_TO {
                resource_id: $resource_id,
                action: $action,
                valid_until: datetime() + duration('P7D')
            }]-())
        AS has_access
        """
        
        result = self.conn.execute(query, {
            "user_id": user_id,
            "resource_id": resource_id,
            "action": action
        }).get_next()
        
        return result[0] if result else False
```

## まとめ

| 機能 | RDB | KuzuDB |
|------|-----|---------|
| 基本RBAC | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 階層ロール | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 動的権限 | ⭐⭐ | ⭐⭐⭐⭐ |
| コンテキスト認可 | ⭐ | ⭐⭐⭐⭐⭐ |
| 権限の可視化 | ⭐ | ⭐⭐⭐⭐⭐ |
| 複雑な条件 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**結論**: KuzuDBは複雑なロールベース認可において、RDBよりも圧倒的に簡単で直感的です。特に：
- 階層的な権限継承
- 動的な権限管理
- コンテキストベースの認可
- 権限パスの可視化

これらの実装がグラフ構造により自然に表現できます。