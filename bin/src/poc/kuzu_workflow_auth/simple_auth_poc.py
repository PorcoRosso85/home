"""
KuzuDB認証認可POC - シンプルな実装例
"""

import kuzu
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class SimpleAuthSystem:
    """シンプルな認証認可システムのPOC"""
    
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """認証認可用のスキーマを初期化"""
        queries = [
            # ユーザーテーブル
            """CREATE NODE TABLE IF NOT EXISTS User (
                id STRING PRIMARY KEY,
                username STRING,
                email STRING,
                password_hash STRING,
                created_at STRING,
                is_active BOOLEAN DEFAULT true
            )""",
            
            # ロールテーブル
            """CREATE NODE TABLE IF NOT EXISTS Role (
                id STRING PRIMARY KEY,
                name STRING,
                description STRING
            )""",
            
            # セッションテーブル
            """CREATE NODE TABLE IF NOT EXISTS Session (
                id STRING PRIMARY KEY,
                user_id STRING,
                token STRING,
                expires_at STRING,
                created_at STRING
            )""",
            
            # 権限テーブル
            """CREATE NODE TABLE IF NOT EXISTS Permission (
                id STRING PRIMARY KEY,
                resource STRING,
                action STRING,
                role_id STRING
            )""",
            
            # リレーションシップ
            """CREATE REL TABLE IF NOT EXISTS HAS_ROLE (
                FROM User TO Role,
                assigned_at STRING
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS HAS_SESSION (
                FROM User TO Session
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS HAS_PERMISSION (
                FROM Role TO Permission
            )"""
        ]
        
        for query in queries:
            self.conn.execute(query)
    
    def create_user(self, username: str, email: str, password: str) -> str:
        """ユーザーを作成"""
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        query = """
        CREATE (u:User {
            id: $id,
            username: $username,
            email: $email,
            password_hash: $password_hash,
            created_at: $created_at
        })
        """
        
        self.conn.execute(query, {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat()
        })
        
        return user_id
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """ユーザー認証してセッショントークンを返す"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        query = """
        MATCH (u:User)
        WHERE u.username = $username 
          AND u.password_hash = $password_hash
          AND u.is_active = true
        RETURN u.id
        """
        
        result = self.conn.execute(query, {
            "username": username,
            "password_hash": password_hash
        }).get_next()
        
        if result:
            user_id = result[0]
            return self._create_session(user_id)
        
        return None
    
    def _create_session(self, user_id: str) -> str:
        """セッションを作成"""
        session_id = f"session_{secrets.token_hex(16)}"
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        query = """
        MATCH (u:User {id: $user_id})
        CREATE (s:Session {
            id: $session_id,
            user_id: $user_id,
            token: $token,
            expires_at: $expires_at,
            created_at: $created_at
        })
        CREATE (u)-[:HAS_SESSION]->(s)
        """
        
        self.conn.execute(query, {
            "user_id": user_id,
            "session_id": session_id,
            "token": token,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()
        })
        
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """トークンを検証してユーザーIDを返す"""
        query = """
        MATCH (u:User)-[:HAS_SESSION]->(s:Session)
        WHERE s.token = $token
          AND s.expires_at > $now
        RETURN u.id
        """
        
        result = self.conn.execute(query, {
            "token": token,
            "now": datetime.now().isoformat()
        }).get_next()
        
        return result[0] if result else None
    
    def assign_role(self, user_id: str, role_name: str):
        """ユーザーにロールを割り当て"""
        role_id = f"role_{role_name}"
        
        # ロールが存在しない場合は作成
        self.conn.execute("""
            CREATE (r:Role {id: $id, name: $name})
            ON CONFLICT DO NOTHING
        """, {"id": role_id, "name": role_name})
        
        # ユーザーにロールを割り当て
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (r:Role {id: $role_id})
        CREATE (u)-[:HAS_ROLE {assigned_at: $assigned_at}]->(r)
        """
        
        self.conn.execute(query, {
            "user_id": user_id,
            "role_id": role_id,
            "assigned_at": datetime.now().isoformat()
        })
    
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """ユーザーが特定のリソースに対する権限を持っているか確認"""
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(r:Role)-[:HAS_PERMISSION]->(p:Permission)
        WHERE p.resource = $resource AND p.action = $action
        RETURN count(p) > 0
        """
        
        result = self.conn.execute(query, {
            "user_id": user_id,
            "resource": resource,
            "action": action
        }).get_next()
        
        return result[0] if result else False


class WorkflowPOC:
    """シンプルなワークフローシステムのPOC"""
    
    def __init__(self, conn: kuzu.Connection):
        self.conn = conn
        self._initialize_workflow_schema()
    
    def _initialize_workflow_schema(self):
        """ワークフロー用のスキーマを初期化"""
        queries = [
            """CREATE NODE TABLE IF NOT EXISTS WorkflowDefinition (
                id STRING PRIMARY KEY,
                name STRING,
                states STRING,  -- JSON array
                transitions STRING  -- JSON object
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS WorkflowInstance (
                id STRING PRIMARY KEY,
                definition_id STRING,
                entity_id STRING,
                current_state STRING,
                created_at STRING,
                updated_at STRING
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS FOLLOWS_WORKFLOW (
                FROM RequirementEntity TO WorkflowInstance
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS WORKFLOW_TRANSITION (
                FROM WorkflowInstance TO WorkflowInstance,
                from_state STRING,
                to_state STRING,
                triggered_by STRING,
                triggered_at STRING
            )"""
        ]
        
        for query in queries:
            self.conn.execute(query)
    
    def create_workflow_definition(self, name: str, states: List[str], 
                                 transitions: Dict[str, List[str]]) -> str:
        """ワークフロー定義を作成"""
        import json
        
        workflow_id = f"workflow_{secrets.token_hex(8)}"
        
        query = """
        CREATE (w:WorkflowDefinition {
            id: $id,
            name: $name,
            states: $states,
            transitions: $transitions
        })
        """
        
        self.conn.execute(query, {
            "id": workflow_id,
            "name": name,
            "states": json.dumps(states),
            "transitions": json.dumps(transitions)
        })
        
        return workflow_id
    
    def start_workflow(self, definition_id: str, entity_id: str, 
                      initial_state: str) -> str:
        """ワークフローインスタンスを開始"""
        instance_id = f"instance_{secrets.token_hex(8)}"
        
        query = """
        CREATE (wi:WorkflowInstance {
            id: $id,
            definition_id: $definition_id,
            entity_id: $entity_id,
            current_state: $current_state,
            created_at: $created_at,
            updated_at: $updated_at
        })
        """
        
        self.conn.execute(query, {
            "id": instance_id,
            "definition_id": definition_id,
            "entity_id": entity_id,
            "current_state": initial_state,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        # エンティティとワークフローを関連付け
        self.conn.execute("""
            MATCH (e:RequirementEntity {id: $entity_id})
            MATCH (wi:WorkflowInstance {id: $instance_id})
            CREATE (e)-[:FOLLOWS_WORKFLOW]->(wi)
        """, {"entity_id": entity_id, "instance_id": instance_id})
        
        return instance_id
    
    def transition_workflow(self, instance_id: str, to_state: str, 
                          triggered_by: str) -> bool:
        """ワークフローの状態を遷移"""
        # 現在の状態と定義を取得
        query = """
        MATCH (wi:WorkflowInstance {id: $instance_id})
        MATCH (wd:WorkflowDefinition {id: wi.definition_id})
        RETURN wi.current_state, wd.transitions
        """
        
        result = self.conn.execute(query, {"instance_id": instance_id}).get_next()
        if not result:
            return False
        
        import json
        current_state = result[0]
        transitions = json.loads(result[1])
        
        # 遷移が有効か確認
        if current_state not in transitions or to_state not in transitions[current_state]:
            return False
        
        # 状態を更新
        update_query = """
        MATCH (wi:WorkflowInstance {id: $instance_id})
        SET wi.current_state = $to_state,
            wi.updated_at = $updated_at
        """
        
        self.conn.execute(update_query, {
            "instance_id": instance_id,
            "to_state": to_state,
            "updated_at": datetime.now().isoformat()
        })
        
        return True


# 使用例
if __name__ == "__main__":
    # 認証システムの初期化
    auth = SimpleAuthSystem("./auth_poc.db")
    
    # ユーザー作成
    user_id = auth.create_user("john_doe", "john@example.com", "password123")
    print(f"Created user: {user_id}")
    
    # 認証
    token = auth.authenticate("john_doe", "password123")
    print(f"Authentication token: {token}")
    
    # トークン検証
    validated_user = auth.validate_token(token)
    print(f"Validated user: {validated_user}")
    
    # ロール割り当て
    auth.assign_role(user_id, "admin")
    
    # ワークフローシステムの初期化
    workflow = WorkflowPOC(auth.conn)
    
    # ワークフロー定義作成
    workflow_def_id = workflow.create_workflow_definition(
        name="要件承認ワークフロー",
        states=["draft", "review", "approved", "rejected"],
        transitions={
            "draft": ["review"],
            "review": ["approved", "rejected", "draft"],
            "approved": [],
            "rejected": ["draft"]
        }
    )
    
    print(f"Created workflow definition: {workflow_def_id}")