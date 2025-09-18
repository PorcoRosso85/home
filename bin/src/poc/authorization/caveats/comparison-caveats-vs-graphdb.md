# SpiceDB Caveats vs GraphDB認可拡張 比較分析

## 概要比較

### SpiceDB with Caveats
```
┌─────────────────────────────────────────────────┐
│                 SpiceDB                         │
│                                                 │
│  ┌─────────────┐    ┌─────────────────────┐   │
│  │   Schema    │    │     Caveats         │   │
│  │ (静的関係)  │ +  │ (動的条件評価)      │   │
│  └─────────────┘    └─────────────────────┘   │
│                                                 │
│  例: document#viewer@user[time_limit_caveat]   │
└─────────────────────────────────────────────────┘

利点:
- 条件付き権限の標準サポート
- CEL（Common Expression Language）で柔軟な条件記述
- 権限チェック時に動的評価

課題:
- 別システムとの同期が必要
- Caveatsの複雑な条件はパフォーマンス影響
```

### GraphDB（例：KuzuDB）での認可拡張
```
┌─────────────────────────────────────────────────┐
│              GraphDB (KuzuDB)                   │
│                                                 │
│  (:User)-[:HAS_PERMISSION {                     │
│     type: "view",                               │
│     expires_at: "2024-12-31T23:59:59Z",       │
│     ip_range: "10.0.0.0/8",                   │
│     conditions: {...}                           │
│  }]->(:Resource)                                │
│                                                 │
│  Cypherクエリで条件評価                         │
└─────────────────────────────────────────────────┘

利点:
- アプリデータと同じDBで管理
- 同期問題なし
- グラフ走査で複雑な権限継承を表現

課題:
- 認可ロジックの自前実装が必要
- 標準化されていない
```

## 詳細比較

### 1. 条件付き権限の実装

#### SpiceDB Caveats
```zaml
definition document {
    relation viewer: user with expiry_caveat
    permission view = viewer
}

caveat expiry_caveat(current_time timestamp, expiry_time timestamp) {
    current_time < expiry_time
}

// 使用例
document:doc1#viewer@user:alice[expiry_caveat:{"expiry_time":"2024-12-31"}]
```

#### GraphDB拡張
```cypher
// 権限エッジに属性を持たせる
CREATE (u:User {id: 'alice'})-[:CAN_VIEW {
    expires_at: datetime('2024-12-31T23:59:59Z'),
    ip_ranges: ['10.0.0.0/8', '192.168.0.0/16'],
    conditions: {
        require_2fa: true,
        allowed_hours: '09:00-18:00'
    }
}]->(d:Document {id: 'doc1'})

// 権限チェッククエリ
MATCH (u:User {id: $userId})-[p:CAN_VIEW]->(d:Document {id: $docId})
WHERE p.expires_at > datetime()
  AND $userIp IN p.ip_ranges
  AND ($user2faVerified = true OR p.conditions.require_2fa = false)
RETURN COUNT(p) > 0 as hasPermission
```

### 2. パフォーマンス比較

#### SpiceDB
```
権限チェック: ~5-50ms
- 関係の検索: 2-10ms
- Caveat評価: 3-40ms（条件の複雑さに依存）

スケーラビリティ:
- 水平スケール可能
- キャッシュ効率的
```

#### GraphDB
```
権限チェック: ~1-20ms
- グラフ走査: 1-15ms
- 条件評価: 0-5ms（DB内で完結）

スケーラビリティ:
- DBのスケーラビリティに依存
- 複雑なグラフ走査は重い
```

### 3. 実装の複雑さ

#### SpiceDB Caveats
```python
# シンプルな実装
async def check_permission(user_id, resource_id, permission):
    result = await spicedb.check_permission(
        resource=f"document:{resource_id}",
        permission=permission,
        subject=f"user:{user_id}",
        context={
            "current_time": datetime.utcnow().isoformat(),
            "request_ip": request.client.host,
            "user_2fa_verified": user.is_2fa_verified
        }
    )
    return result.permissionship == "HAS_PERMISSION"
```

#### GraphDB拡張
```python
# より複雑な実装が必要
async def check_permission(user_id, resource_id, permission):
    query = """
    MATCH (u:User {id: $userId})-[p:HAS_PERMISSION]->(r:Resource {id: $resourceId})
    WHERE p.type = $permission
      AND (p.expires_at IS NULL OR p.expires_at > datetime())
      AND CASE 
        WHEN p.ip_ranges IS NOT NULL 
        THEN ANY(range IN p.ip_ranges WHERE ip_in_range($userIp, range))
        ELSE true
      END
      // さらに条件を追加...
    RETURN COUNT(p) > 0 as hasPermission
    """
    
    result = await graphdb.query(query, {
        "userId": user_id,
        "resourceId": resource_id,
        "permission": permission,
        "userIp": request.client.host
    })
    return result[0]["hasPermission"]
```

## 使い分けの指針

### SpiceDB Caveatsを選ぶべき場合

1. **標準化された認可が必要**
   - 業界標準のReBAC実装
   - 監査要件が厳しい

2. **複雑な条件付き権限**
   - 時間、場所、デバイス、認証レベルなど
   - CELで表現可能な複雑なビジネスルール

3. **マイクロサービス環境**
   - 認可を独立したサービスとして管理
   - 複数のアプリケーションから利用

### GraphDB拡張を選ぶべき場合

1. **シンプルな統合**
   - 既存のGraphDBを活用
   - 同期問題を避けたい

2. **高度なグラフ分析との統合**
   ```cypher
   // 例：ソーシャルグラフと権限の組み合わせ
   MATCH (user:User {id: $userId})-[:FOLLOWS*1..2]->(influencer:User)
         -[:CAN_VIEW]->(content:Content)
   WHERE influencer.verified = true
   RETURN DISTINCT content
   ```

3. **カスタム要件**
   - 標準的でない独自の権限モデル
   - アプリケーション固有の最適化

## ハイブリッドアプローチ

```
┌─────────────────────┐     ┌─────────────────────┐
│     GraphDB         │     │     SpiceDB         │
│                     │     │                     │
│  基本的な関係と     │     │  条件付き権限      │
│  静的な権限         │────▶│  (Caveats)         │
│                     │     │                     │
│  - ユーザー情報     │     │  - 時間制限        │
│  - 組織構造         │     │  - IP制限          │
│  - 基本的な役割     │     │  - 承認フロー      │
└─────────────────────┘     └─────────────────────┘

// GraphDBで基本チェック
if (await graphdb.hasBasicPermission(user, resource)) {
    // SpiceDBで条件付きチェック
    return await spicedb.checkWithCaveats(user, resource, context);
}
```

## 推奨

**段階的アプローチ**をお勧めします：

1. **Phase 1**: GraphDBで基本的な認可を実装
   - シンプルな役割ベースアクセス制御
   - 同期問題なし

2. **Phase 2**: 条件付き権限が必要になったらSpiceDB Caveats
   - 時間制限、IP制限などの高度な要件
   - 既存のGraphDB実装と併用

3. **Phase 3**: 要件に応じて統合または移行
   - 全面的にSpiceDBへ移行
   - またはハイブリッドで運用継続

この段階的アプローチにより、過度な複雑性を避けながら、必要に応じて高度な機能を追加できます。