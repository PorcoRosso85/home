# リアルタイム同期パターンのASCII図解

## パターン1: 同期的二重書き込み（非推奨）

```
ユーザー作成リクエスト
        │
        ▼
┌─────────────────┐
│   App Server    │
│                 │
│  async def      │
│  create_user(): │
│    ├─────────────────────┐
│    │                     │
│    ▼                     ▼
│  ┌──────────┐      ┌──────────┐
│  │ App DB   │      │ SpiceDB  │
│  │ INSERT   │      │  Write   │
│  └──────────┘      └──────────┘
│    │                     │
│    └──────┬──────────────┘
│           │
│         両方成功？
│           │
│    ┌──────┴──────┐
│    │ Yes    No   │
│    ▼        ▼    │
│  Return   Rollback│
│  Success  両方    │
└─────────────────┘

問題点:
- トランザクション境界を跨ぐ
- SpiceDB障害時にユーザー作成が失敗
- レイテンシの増加
```

## パターン2: 非同期イベント駆動（推奨）

```
ユーザー作成リクエスト
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                     App Server                          │
│                                                         │
│  async def create_user():                              │
│    1. DB保存          2. イベント発行                   │
│       ▼                    ▼                           │
│  ┌──────────┐        ┌─────────────┐                  │
│  │ App DB   │        │Event Queue  │                  │
│  │ INSERT   │        │(Kafka/NATS) │                  │
│  └──────────┘        └──────┬──────┘                  │
│       │                     │                          │
│       ▼                     │ 非同期                   │
│    Return                   │                          │
│    Success ─────────────────┼───────────────────────▶ │
│    (即座に)                 │                     Response
└─────────────────────────────┼───────────────────────────┘
                              │
                              │ 数ミリ秒後
                              ▼
                    ┌─────────────────┐      ┌──────────┐
                    │  Sync Service   │─────▶│ SpiceDB  │
                    │ (Event Handler) │      │  Write   │
                    └─────────────────┘      └──────────┘

利点:
- アプリの応答速度維持
- 障害の分離（SpiceDB障害でもユーザー作成は成功）
- リトライ可能
```

## パターン3: Outboxパターン（トランザクション保証付き）

```
ユーザー作成リクエスト
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                   App Server                         │
│                                                      │
│  async def create_user():                           │
│    ┌─────────── DB Transaction ──────────┐          │
│    │                                      │          │
│    │  1. INSERT INTO users (...)         │          │
│    │  2. INSERT INTO outbox_events (     │          │
│    │       event_type: 'user.created',   │          │
│    │       payload: {...},               │          │
│    │       status: 'pending'             │          │
│    │     )                               │          │
│    └──────────────────────────────────────┘          │
│                      │                               │
│                      ▼                               │
│                   COMMIT ────────────────────────▶ Response
└──────────────────────────────────────────────────────┘
                      
        別プロセス（Outbox Publisher）
        ┌────────────────────────────┐
        │  while True:               │
        │    1. SELECT * FROM outbox │
        │       WHERE status='pending'│
        │    2. Publish to Queue     │
        │    3. UPDATE status='sent' │
        └─────────────┬──────────────┘
                      │
                      ▼
              ┌─────────────┐
              │Event Queue  │
              └──────┬──────┘
                     │
                     ▼
           ┌─────────────────┐      ┌──────────┐
           │  Sync Service   │─────▶│ SpiceDB  │
           └─────────────────┘      └──────────┘

利点:
- トランザクション保証（イベントの喪失なし）
- At-least-once配信保証
- 監査ログ自動生成
```

## パターン4: CDC（Change Data Capture）

```
ユーザー作成リクエスト
        │
        ▼
┌─────────────────┐
│   App Server    │
│                 │
│ create_user():  │
│   INSERT INTO   │
│   users (...)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      PostgreSQL WAL
│   PostgreSQL    │ ─────────────────────┐
│                 │                      │
│  ┌───────────┐  │                      ▼
│  │users table│  │            ┌─────────────────┐
│  └───────────┘  │            │   Debezium      │
└─────────────────┘            │  (CDC Tool)     │
                               │                 │
                               │ 1. WAL読み取り  │
                               │ 2. 変更検出     │
                               │ 3. イベント生成 │
                               └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────┐
                               │ Kafka Topic │
                               │user-changes │
                               └──────┬──────┘
                                      │
                                      ▼
                            ┌─────────────────┐      ┌──────────┐
                            │ Transform/Sync  │─────▶│ SpiceDB  │
                            │    Service      │      └──────────┘
                            └─────────────────┘

利点:
- アプリケーション無変更
- 既存システムに後付け可能
- データベースレベルの保証
```

## 実装例: イベント駆動パターン

### アプリケーションサーバー側

```python
# app_server.py
class UserService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus
    
    async def create_user(self, user_data):
        # 1. AppDBに保存（これで即座にレスポンス可能）
        async with self.db.transaction() as tx:
            user = await tx.users.insert({
                'id': generate_uuid(),
                'email': user_data['email'],
                'name': user_data['name'],
                'org_id': user_data['org_id'],
                'created_at': datetime.utcnow()
            })
            
            # 2. イベント発行（非同期）
            await self.event_bus.publish('user.created', {
                'user_id': user['id'],
                'org_id': user['org_id'],
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # 3. 即座にレスポンス（SpiceDBの更新を待たない）
        return {'user_id': user['id'], 'status': 'created'}
```

### 同期サービス側

```python
# sync_service.py
class SpiceDBSyncService:
    def __init__(self, spicedb_client, event_bus):
        self.spicedb = spicedb_client
        self.event_bus = event_bus
    
    async def start(self):
        # イベントをサブスクライブ
        await self.event_bus.subscribe('user.created', self.on_user_created)
    
    async def on_user_created(self, event):
        """ユーザー作成イベントを受信してSpiceDBに同期"""
        try:
            # SpiceDBに権限関係を作成
            await self.spicedb.WriteRelationships([
                # ユーザーを組織のメンバーとして追加
                Relationship(
                    resource=ObjectReference(
                        object_type="organization",
                        object_id=event['org_id']
                    ),
                    relation="member",
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type="user",
                            object_id=event['user_id']
                        )
                    )
                )
            ])
            
            # 成功をログ
            logger.info(f"Synced user {event['user_id']} to SpiceDB")
            
        except Exception as e:
            # 失敗時はリトライキューへ
            await self.handle_sync_failure(event, e)
```

## タイミング図

```
時間軸 ─────────────────────────────────────────────▶

Client    AppServer    AppDB    EventQueue    SyncService    SpiceDB
  │          │           │          │             │             │
  │ POST     │           │          │             │             │
  │ /users   │           │          │             │             │
  ├─────────▶│           │          │             │             │
  │          │ INSERT    │          │             │             │
  │          ├──────────▶│          │             │             │
  │          │     OK    │          │             │             │
  │          │◀──────────┤          │             │             │
  │          │ publish   │          │             │             │
  │          ├───────────┼─────────▶│             │             │
  │   201    │           │          │             │             │
  │◀─────────┤           │          │             │             │
  │ Created  │           │          │ event       │             │
  │          │           │          ├────────────▶│             │
  │          │           │          │             │ write       │
  │          │           │          │             ├────────────▶│
  │          │           │          │             │      OK     │
  │          │           │          │             │◀────────────┤
  
  └─ 数ms ──┘                                    └─ 数十ms ────┘
   (即レスポンス)                                 (非同期で同期)
```

## まとめ

- **同期的二重書き込み**: シンプルだが本番環境では避けるべき
- **非同期イベント駆動**: 最もバランスが良く、推奨
- **Outboxパターン**: トランザクション保証が必要な場合
- **CDC**: 既存システムを変更できない場合

ほとんどの場合、**非同期イベント駆動パターン**が最適です。ユーザー作成は即座に完了し、権限情報は数ミリ秒〜数秒後にSpiceDBに反映されます。