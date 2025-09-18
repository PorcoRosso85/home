# SpiceDB同期アーキテクチャ設計

## 概要

アプリケーションDB（ユーザーデータ）とSpiceDB（認可データ）を独立したサービスとして運用する際の同期戦略。

## アーキテクチャパターン

### 1. イベント駆動同期（推奨）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   App Server    │────▶│   App DB        │────▶│  Event Stream   │
│                 │     │  (PostgreSQL)   │     │ (Kafka/NATS)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                              ┌───────────────────────────┘
                              ▼
                    ┌─────────────────┐     ┌─────────────────┐
                    │  Sync Service   │────▶│    SpiceDB      │
                    │                 │     │                 │
                    └─────────────────┘     └─────────────────┘

利点：
- リアルタイム性（数ミリ秒〜数秒）
- 耐障害性（イベントストリームによる再送）
- 監査証跡の自動記録
```

### 2. CDC（Change Data Capture）同期

```
┌─────────────────┐     ┌─────────────────┐
│   App DB        │────▶│   CDC Tool      │
│  (PostgreSQL)   │     │  (Debezium)    │
└─────────────────┘     └────────┬────────┘
     ▲                           │
     │                           ▼
     │                 ┌─────────────────┐     ┌─────────────────┐
     │                 │ Transform/Filter│────▶│    SpiceDB      │
     │                 │    Service      │     │                 │
     │                 └─────────────────┘     └─────────────────┘
     │
     └─── WAL（Write-Ahead Log）を監視

利点：
- アプリケーション側の変更不要
- 全ての変更を確実にキャプチャ
- 既存システムへの影響最小
```

### 3. バッチ同期（シンプルだが制限あり）

```
┌─────────────────┐              ┌─────────────────┐
│   App DB        │              │    SpiceDB      │
│                 │              │                 │
└────────┬────────┘              └────────▲────────┘
         │                                 │
         │      ┌─────────────────┐       │
         └─────▶│  Batch Sync Job │───────┘
                │  (Cron/Airflow) │
                └─────────────────┘

実行タイミング：
- 定期実行（5分、1時間、日次など）
- トリガー実行（ユーザー操作後）

利点：
- 実装がシンプル
- 大量データの初期同期に適している
問題点：
- 遅延が発生（同期間隔に依存）
- 同期中の不整合状態
```

## 実装例

### イベント駆動同期の実装

```python
# app_server.py
from typing import Dict, Any
import asyncio
from nats.aio.client import Client as NATS

class UserService:
    def __init__(self, db, event_publisher):
        self.db = db
        self.event_publisher = event_publisher
    
    async def create_user(self, user_data: Dict[str, Any]):
        # 1. アプリDBに保存
        user = await self.db.users.create(user_data)
        
        # 2. イベント発行
        await self.event_publisher.publish("user.created", {
            "user_id": user.id,
            "org_id": user.org_id,
            "role": user.role,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return user
    
    async def assign_role(self, user_id: str, role: str, resource_id: str):
        # 1. アプリDBに保存
        await self.db.roles.create({
            "user_id": user_id,
            "role": role,
            "resource_id": resource_id
        })
        
        # 2. イベント発行
        await self.event_publisher.publish("role.assigned", {
            "user_id": user_id,
            "role": role,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat()
        })
```

```python
# sync_service.py
import asyncio
from authzed.api.v1 import Client as SpiceDBClient
from nats.aio.client import Client as NATS

class SpiceDBSyncService:
    def __init__(self, spicedb_client, nats_client):
        self.spicedb = spicedb_client
        self.nats = nats_client
    
    async def start(self):
        # イベントサブスクリプション
        await self.nats.subscribe("user.created", self.handle_user_created)
        await self.nats.subscribe("role.assigned", self.handle_role_assigned)
        await self.nats.subscribe("user.deleted", self.handle_user_deleted)
    
    async def handle_user_created(self, msg):
        data = json.loads(msg.data.decode())
        
        # SpiceDBに組織メンバーシップを作成
        await self.spicedb.write_relationships([{
            "resource": {"object_type": "organization", "object_id": data["org_id"]},
            "relation": "member",
            "subject": {"object": {"object_type": "user", "object_id": data["user_id"]}}
        }])
    
    async def handle_role_assigned(self, msg):
        data = json.loads(msg.data.decode())
        
        # SpiceDBに権限関係を作成
        await self.spicedb.write_relationships([{
            "resource": {"object_type": "resource", "object_id": data["resource_id"]},
            "relation": data["role"],  # viewer, editor, owner など
            "subject": {"object": {"object_type": "user", "object_id": data["user_id"]}}
        }])
```

### CDC同期の実装

```yaml
# debezium-connector.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: postgres-spicedb-connector
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  config:
    database.hostname: postgres.example.com
    database.port: 5432
    database.user: debezium
    database.password: ${DB_PASSWORD}
    database.dbname: appdb
    table.include.list: public.users,public.roles,public.organizations
    transforms: extractUserId,routeToSpiceDB
    transforms.extractUserId.type: org.apache.kafka.connect.transforms.ExtractField$Value
    transforms.extractUserId.field: after
```

### バッチ同期の実装

```python
# batch_sync.py
import schedule
import time
from datetime import datetime, timedelta

class BatchSyncJob:
    def __init__(self, app_db, spicedb_client):
        self.app_db = app_db
        self.spicedb = spicedb_client
        self.last_sync = datetime.utcnow()
    
    def sync_changes(self):
        """前回の同期以降の変更を同期"""
        # 1. 変更されたユーザーを取得
        changed_users = self.app_db.query("""
            SELECT * FROM users 
            WHERE updated_at > %s
            ORDER BY updated_at
        """, [self.last_sync])
        
        # 2. バッチでSpiceDBに書き込み
        relationships = []
        for user in changed_users:
            relationships.append({
                "resource": {"object_type": "organization", "object_id": user.org_id},
                "relation": "member",
                "subject": {"object": {"object_type": "user", "object_id": user.id}}
            })
        
        if relationships:
            self.spicedb.write_relationships(relationships)
        
        self.last_sync = datetime.utcnow()
    
    def full_sync(self):
        """全データの完全同期（初期化や障害復旧用）"""
        # 既存の関係を削除（オプション）
        # self.spicedb.delete_relationships(...)
        
        # 全ユーザーを同期
        all_users = self.app_db.query("SELECT * FROM users")
        # ... 同期処理
```

## 同期戦略の選択基準

### イベント駆動を選ぶべき場合
- リアルタイム性が重要（数秒以内の反映が必要）
- 監査ログが必要
- マイクロサービスアーキテクチャ
- イベントストリーム基盤がすでにある

### CDCを選ぶべき場合
- レガシーシステムで変更が困難
- 100%の変更キャプチャが必要
- データベース中心のアーキテクチャ
- 複数のアプリが同じDBを更新

### バッチ同期を選ぶべき場合
- 遅延が許容される（分単位〜時間単位）
- システムがシンプル
- 初期プロトタイプ
- データ量が少ない

## ハイブリッドアプローチ

実運用では、これらを組み合わせることが多い：

```
1. 初期データ投入：バッチ同期で全データを同期
2. 運用中：イベント駆動でリアルタイム同期
3. 定期チェック：日次バッチで整合性確認
4. 障害復旧：CDCで欠落データを補完
```

## 考慮事項

### 1. 整合性の保証
```python
# 二相コミットは使わず、結果整合性を採用
async def create_user_with_retry(user_data):
    # 1. アプリDBに保存
    user = await app_db.create_user(user_data)
    
    # 2. SpiceDBに同期（リトライ付き）
    for attempt in range(3):
        try:
            await sync_to_spicedb(user)
            break
        except Exception as e:
            if attempt == 2:
                # 最終的に失敗したら補償トランザクション
                await handle_sync_failure(user)
```

### 2. 同期の監視
```python
# メトリクス収集
class SyncMetrics:
    def __init__(self):
        self.sync_lag_histogram = Histogram('spicedb_sync_lag_seconds')
        self.sync_errors_counter = Counter('spicedb_sync_errors_total')
        self.last_sync_gauge = Gauge('spicedb_last_sync_timestamp')
```

### 3. 障害時の対応
- 同期キューの永続化
- 失敗したイベントのDLQ（Dead Letter Queue）
- 手動での再同期機能

これらの設計により、アプリケーションDBとSpiceDBを疎結合に保ちながら、適切な同期を実現できます。