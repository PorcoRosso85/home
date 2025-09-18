# KuzuDB認証認可ワークフロー実装ガイド

## 実装の簡単さ評価

### 認証認可: ⭐⭐⭐☆☆ (普通)
- **簡単な部分**
  - KuzuDBのグラフ構造はユーザー/ロール/権限の関係性を自然に表現
  - Cypherクエリで権限チェックが直感的
  - 既存のバージョン管理機能を活用可能

- **難しい部分**
  - セキュリティ実装（パスワード管理、トークン管理）
  - 全てのクエリに権限チェックを追加する必要
  - パフォーマンスへの影響

### ワークフロー: ⭐⭐☆☆☆ (やや難しい)
- **簡単な部分**
  - グラフ構造は状態遷移の表現に適している
  - 既存のステータスフィールドを拡張可能
  - 履歴追跡が容易

- **難しい部分**
  - 複雑な条件付き遷移の実装
  - 並行ワークフローの管理
  - イベント駆動の仕組みが必要

## 最小実装プラン（2-3週間）

### Phase 1: 基本認証（1週間）
```python
# 必要最小限の実装
1. ユーザーテーブル追加
2. 簡単なログイン機能
3. セッション管理
4. 既存APIに認証チェック追加
```

### Phase 2: シンプルな権限管理（3-4日）
```python
# ロールベースアクセス制御
1. admin/user/viewerの3ロール
2. 要件の所有者概念
3. 読み取り/書き込み権限
```

### Phase 3: 基本ワークフロー（1週間）
```python
# ステータスベースの承認フロー
1. draft → review → approved/rejected
2. ロールによる承認権限
3. 履歴記録
```

## 実装サンプル

### 1. 権限チェック付きクエリ
```python
def get_requirement_with_auth(req_id: str, user_id: str) -> Optional[Dict]:
    """認証付き要件取得"""
    query = """
    MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(r:Role)
    MATCH (req:RequirementEntity {id: $req_id})
    WHERE r.name IN ['admin', 'user'] 
       OR EXISTS((u)-[:OWNS]->(req))
       OR EXISTS((r)-[:CAN_READ]->(req))
    RETURN req
    """
    # ...
```

### 2. ワークフロー状態遷移
```python
def approve_requirement(req_id: str, approver_id: str) -> bool:
    """要件承認（権限チェック付き）"""
    query = """
    MATCH (u:User {id: $approver_id})-[:HAS_ROLE]->(r:Role {name: 'admin'})
    MATCH (req:RequirementEntity {id: $req_id, status: 'review'})
    SET req.status = 'approved',
        req.approved_by = $approver_id,
        req.approved_at = $timestamp
    RETURN req
    """
    # ...
```

## 既存システムへの統合

### 1. 最小限の変更で統合
```python
# 既存のRepositoryクラスを拡張
class AuthenticatedRequirementRepository(RequirementRepository):
    def __init__(self, conn, auth_service):
        super().__init__(conn)
        self.auth = auth_service
    
    def get_requirement(self, req_id: str, user_token: str):
        # トークン検証
        user_id = self.auth.validate_token(user_token)
        if not user_id:
            raise UnauthorizedException()
        
        # 権限チェック付きクエリ
        return self._get_with_permission_check(req_id, user_id)
```

### 2. デコレータによる権限チェック
```python
def requires_auth(role=None):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            token = kwargs.get('token')
            user_id = self.auth.validate_token(token)
            
            if role and not self.auth.has_role(user_id, role):
                raise ForbiddenException()
            
            kwargs['user_id'] = user_id
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# 使用例
@requires_auth(role='admin')
def delete_requirement(self, req_id: str, **kwargs):
    # 管理者のみ削除可能
    pass
```

## 推奨事項

### すぐに実装可能な機能
1. **基本認証** - ユーザー/パスワード管理
2. **セッション管理** - トークンベース認証
3. **シンプルなロール** - admin/user/viewer
4. **所有者ベースの権限** - 作成者による編集権限

### 段階的に追加する機能
1. **OAuth/OIDC統合** - 外部認証プロバイダー
2. **詳細な権限管理** - リソースレベルの権限
3. **複雑なワークフロー** - 条件分岐、並行承認
4. **監査ログ** - 全操作の記録

## 結論
KuzuDBでの認証認可実装は**中程度の難易度**です。グラフデータベースの特性を活かして、ユーザー/ロール/権限の関係を自然に表現できますが、セキュリティとパフォーマンスの考慮が必要です。

最小実装から始めて、段階的に機能を追加するアプローチが推奨されます。