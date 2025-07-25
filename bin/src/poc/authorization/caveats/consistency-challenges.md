# SpiceDB同期の整合性課題と対策

## 現実的な問題

### 1. ユーザー不整合シナリオ

```
【シナリオ1: ゴーストユーザー問題】

時間軸 ─────────────────────────────────────────────▶

AppDB     SpiceDB    問題
─────     ────────   ─────────────────────────────
User123   -          ユーザー作成
  ↓       
User123   User123    同期完了
  ↓
削除      User123    AppDBから削除されたが...
  ↓
  -       User123    SpiceDBに残存（ゴースト）
                     → 削除されたユーザーが権限を持ち続ける！

【シナリオ2: 権限の遅延反映】

AppDB     SpiceDB    問題
─────     ────────   ─────────────────────────────
Admin     User       ユーザーを管理者に昇格
  ↓       
Admin     User       同期遅延中（5秒〜1分）
                     → この間、管理者権限が必要な操作が失敗！

【シナリオ3: 部分的な同期失敗】

AppDB                SpiceDB              問題
─────                ────────             ─────
User: Active         -                    新規ユーザー
Role: Admin          -                    
Dept: Engineering    User: Active         部分同期
                     Role: -              → 役割情報が欠落！
                     Dept: -              
```

### 2. より深刻な問題

```
【二重権限問題】

1. ユーザーがプロジェクトAの権限を持つ
2. 権限を剥奪（AppDB更新）
3. 同期失敗
4. 新しく別の権限を付与
5. 同期成功
→ SpiceDBに両方の権限が存在してしまう！

【タイミング問題】

Client        AppServer       AppDB        SpiceDB
  │              │              │            │
  │ DELETE       │              │            │
  │ /user/123    │              │            │
  ├─────────────▶│              │            │
  │              │ DELETE       │            │
  │              ├─────────────▶│            │
  │              │              │            │ (まだ権限あり)
  │              │              │            │
  │ CHECK        │              │            │
  │ permission   │              │            │
  ├──────────────┼──────────────┼───────────▶│
  │              │              │            │
  │◀──────────────────────────────────────────┤
  │ ALLOWED!     │              │            │ (削除済みユーザーが
  │              │              │            │  アクセス可能！)
```

## 対策パターン

### パターン1: Source of Truth統一

```
┌─────────────────────────────────────────────────┐
│            統一認証・認可サービス                │
│                                                 │
│  ┌──────────┐    ┌──────────┐   ┌──────────┐  │
│  │  User    │    │  Auth    │   │ AuthZ    │  │
│  │  Store   │───▶│  Logic   │──▶│(SpiceDB) │  │
│  └──────────┘    └──────────┘   └──────────┘  │
│        ▲                               │        │
│        └───────────────────────────────┘        │
│              単一のデータソース                  │
└─────────────────────────────────────────────────┘
         ▲                      ▲
         │                      │
    App Server 1           App Server 2

利点：
- 不整合が原理的に発生しない
- シンプルな実装

欠点：
- 既存システムの大規模改修が必要
- 単一障害点
```

### パターン2: 同期検証メカニズム

```python
class ConsistencyChecker:
    """定期的に整合性をチェックし、不整合を検出・修復"""
    
    async def check_consistency(self):
        # 1. AppDBの全ユーザーを取得
        app_users = await self.app_db.get_all_users()
        
        # 2. SpiceDBの全ユーザー関係を取得
        spice_relations = await self.spicedb.read_relationships(
            resource_type="user"
        )
        
        # 3. 差分検出
        app_user_ids = {u.id for u in app_users}
        spice_user_ids = {r.subject.id for r in spice_relations}
        
        # ゴーストユーザー（SpiceDBにのみ存在）
        ghosts = spice_user_ids - app_user_ids
        
        # 未同期ユーザー（AppDBにのみ存在）
        missing = app_user_ids - spice_user_ids
        
        # 4. 修復
        await self.remove_ghosts(ghosts)
        await self.sync_missing(missing)
        
        # 5. 権限の詳細チェック
        for user_id in app_user_ids:
            await self.verify_permissions(user_id)
```

### パターン3: 補償トランザクション

```
【削除時の確実な同期】

async def delete_user(user_id):
    # 1. SpiceDBから先に削除（失敗したら中断）
    try:
        await spicedb.delete_all_relationships(
            subject=f"user:{user_id}"
        )
    except Exception:
        raise Exception("Cannot delete user: authorization cleanup failed")
    
    # 2. AppDBから削除
    try:
        await app_db.delete_user(user_id)
    except Exception:
        # AppDB削除失敗時は、SpiceDBに復元
        await restore_user_permissions(user_id)
        raise
    
    # 3. 削除確認ログ
    await audit_log.record(f"User {user_id} deleted from both systems")
```

### パターン4: Hybrid Approach（実用的）

```
┌─────────────────────────────────────────────────────┐
│                  実装推奨構成                       │
│                                                     │
│  1. 基本同期：イベント駆動（通常時）                │
│     └─ 99.9%のケースで十分                         │
│                                                     │
│  2. 整合性チェック：定期バッチ（1時間ごと）        │
│     └─ 不整合を検出して通知                        │
│                                                     │
│  3. 重要操作：同期確認                             │
│     └─ 権限昇格、削除などは同期完了を待つ          │
│                                                     │
│  4. 監視：メトリクスとアラート                     │
│     └─ 同期遅延、エラー率を監視                    │
└─────────────────────────────────────────────────────┘
```

## 実装例：重要操作での同期確認

```python
class CriticalOperationService:
    """重要な操作では同期を確認"""
    
    async def promote_to_admin(self, user_id: str):
        # 1. AppDBで権限変更
        await self.app_db.update_user_role(user_id, "admin")
        
        # 2. SpiceDBへの同期を明示的に実行
        await self.sync_service.sync_user_now(user_id)
        
        # 3. 同期確認（最大5秒待機）
        for i in range(50):
            if await self.verify_admin_in_spicedb(user_id):
                break
            await asyncio.sleep(0.1)
        else:
            # 同期タイムアウト
            await self.app_db.update_user_role(user_id, "user")  # ロールバック
            raise Exception("Failed to sync admin promotion")
        
        return {"status": "promoted", "sync": "confirmed"}
    
    async def delete_user(self, user_id: str):
        # 削除は必ず両方から削除を確認
        # 1. まずSpiceDBから削除
        await self.spicedb.delete_user_completely(user_id)
        
        # 2. 次にAppDBから削除
        await self.app_db.delete_user(user_id)
        
        # 3. 削除確認
        if await self.user_exists_anywhere(user_id):
            raise Exception("User deletion incomplete")
```

## 監視とアラート

```yaml
# prometheus-rules.yaml
groups:
  - name: spicedb_consistency
    rules:
      - alert: HighSyncLatency
        expr: spicedb_sync_latency_seconds > 5
        for: 5m
        annotations:
          summary: "SpiceDB sync latency is high"
          
      - alert: SyncFailureRate
        expr: rate(spicedb_sync_failures[5m]) > 0.01
        annotations:
          summary: "SpiceDB sync failure rate > 1%"
          
      - alert: GhostUsersDetected  
        expr: spicedb_ghost_users_count > 0
        for: 10m
        annotations:
          summary: "Ghost users found in SpiceDB"
```

## 結論

**「SpiceDBに許認可書ければそれで終わり」ではありません。**

実運用では：
1. **整合性監視**が必須
2. **重要操作での同期確認**が必要
3. **定期的な整合性チェック**でゴーストを除去
4. **補償トランザクション**で障害時の一貫性を保つ

これらの対策なしでは、削除されたユーザーがアクセスし続ける、権限変更が反映されないなど、深刻なセキュリティ問題が発生します。