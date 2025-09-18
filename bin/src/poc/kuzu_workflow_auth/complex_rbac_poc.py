"""
KuzuDB複雑なRBACのPOC - RDBでは実装が困難な例
"""

import kuzu
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class ComplexRBACSystem:
    """RDBでは複雑になる認可パターンの実装例"""
    
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """複雑なRBAC用スキーマ"""
        queries = [
            # ロール階層
            """CREATE REL TABLE IF NOT EXISTS INHERITS (
                FROM Role TO Role,
                inherit_permissions BOOLEAN DEFAULT true
            )""",
            
            # 動的権限
            """CREATE REL TABLE IF NOT EXISTS HAS_TEMPORARY_PERMISSION (
                FROM User TO Permission,
                granted_by STRING,
                granted_at STRING,
                expires_at STRING,
                reason STRING
            )""",
            
            # 委任
            """CREATE REL TABLE IF NOT EXISTS DELEGATES_TO (
                FROM User TO User,
                role_id STRING,
                resource_pattern STRING,
                valid_until STRING
            )""",
            
            # コンテキスト権限
            """CREATE REL TABLE IF NOT EXISTS CAN_ACCESS_IN_CONTEXT (
                FROM Role TO Resource,
                context_type STRING,  -- 'owner', 'department', 'project'
                conditions STRING     -- JSON conditions
            )"""
        ]
        
        for query in queries:
            try:
                self.conn.execute(query)
            except:
                pass

    def example_1_hierarchical_roles(self):
        """例1: 階層ロール - CEOは全部門の権限を持つ"""
        print("\n=== 階層ロールの例 ===")
        
        # RDBでは再帰CTEが必要で複雑
        # KuzuDBでは直感的
        query = """
        // CEOの権限チェック - 全ての下位ロールの権限も持つ
        MATCH (u:User {name: 'CEO'})-[:HAS_ROLE]->(:Role {name: 'CEO'})
              -[:INHERITS*0..]->(r:Role)-[:CAN_PERFORM]->(p:Permission)
        RETURN DISTINCT p.resource, p.action
        ORDER BY p.resource
        """
        
        print("CEOは階層的に全ての権限を継承:")
        result = self.conn.execute(query)
        while result.has_next():
            resource, action = result.get_next()
            print(f"  - {resource}: {action}")

    def example_2_context_based_access(self, user_id: str, resource_id: str):
        """例2: コンテキストベースアクセス - 複数の条件でアクセス可能"""
        print("\n=== コンテキストベースアクセス ===")
        
        # RDBでは大量のJOINとOR条件が必要
        # KuzuDBでは複数のパスを自然に表現
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (r:Resource {id: $resource_id})
        
        WITH u, r,
        // パス1: 所有者
        EXISTS((r)-[:OWNED_BY]->(u)) AS is_owner,
        
        // パス2: 同じ部門
        EXISTS((u)-[:BELONGS_TO]->(:Department)<-[:BELONGS_TO]-(r)) AS same_dept,
        
        // パス3: プロジェクトメンバー
        EXISTS((u)-[:MEMBER_OF]->(:Project)<-[:BELONGS_TO]-(r)) AS project_member,
        
        // パス4: 上司の承認済み
        EXISTS((u)<-[:REPORTS_TO*1..3]-(:User)<-[:APPROVED_BY]-(r)) AS approved_by_supervisor,
        
        // パス5: 期限付き権限
        EXISTS((u)-[:HAS_TEMPORARY_PERMISSION {expires_at > $now}]->
               (:Permission {resource_id: $resource_id})) AS has_temp_permission
        
        RETURN {
            can_access: is_owner OR same_dept OR project_member 
                       OR approved_by_supervisor OR has_temp_permission,
            reasons: [
                CASE WHEN is_owner THEN '所有者' END,
                CASE WHEN same_dept THEN '同部門' END,
                CASE WHEN project_member THEN 'プロジェクトメンバー' END,
                CASE WHEN approved_by_supervisor THEN '上司承認済み' END,
                CASE WHEN has_temp_permission THEN '一時的権限' END
            ]
        } AS access_info
        """
        
        result = self.conn.execute(query, {
            "user_id": user_id,
            "resource_id": resource_id,
            "now": datetime.now().isoformat()
        }).get_next()
        
        if result:
            info = result[0]
            print(f"アクセス可能: {info['can_access']}")
            print(f"理由: {[r for r in info['reasons'] if r]}")

    def example_3_delegation_chain(self, original_user: str, delegated_user: str):
        """例3: 権限委任チェーン - AさんがBさんに、BさんがCさんに委任"""
        print("\n=== 権限委任チェーン ===")
        
        # RDBでは委任の追跡が非常に複雑
        # KuzuDBでは委任パスを簡単に追跡
        query = """
        // 委任チェーンを可視化
        MATCH path = (original:User {id: $original})-[:DELEGATES_TO*1..3]->
                     (final:User {id: $delegated})
        WITH path, 
             [rel in relationships(path) | {
                 from: startNode(rel).name,
                 to: endNode(rel).name,
                 role: rel.role_id,
                 expires: rel.valid_until
             }] AS delegation_chain
        
        // 有効な委任かチェック
        WHERE ALL(rel IN relationships(path) WHERE rel.valid_until > $now)
        
        RETURN delegation_chain
        """
        
        result = self.conn.execute(query, {
            "original": original_user,
            "delegated": delegated_user,
            "now": datetime.now().isoformat()
        }).get_next()
        
        if result:
            chain = result[0]
            print("委任チェーン:")
            for step in chain:
                print(f"  {step['from']} → {step['to']} (役割: {step['role']})")

    def example_4_conflict_detection(self):
        """例4: 権限競合検出 - 相反する権限を持つユーザーを検出"""
        print("\n=== 権限競合検出 ===")
        
        # RDBでは競合検出が困難
        # KuzuDBではパターンマッチングで簡単
        query = """
        // 承認者と申請者の両方の権限を持つユーザー（職務分離違反）
        MATCH (u:User)-[:HAS_ROLE]->(r1:Role)-[:CAN_PERFORM]->
              (p1:Permission {action: 'approve'})
        MATCH (u)-[:HAS_ROLE]->(r2:Role)-[:CAN_PERFORM]->
              (p2:Permission {action: 'submit'})
        WHERE p1.resource_type = p2.resource_type
        
        RETURN u.name AS user, 
               collect(DISTINCT r1.name) AS approver_roles,
               collect(DISTINCT r2.name) AS submitter_roles
        """
        
        print("職務分離違反の可能性:")
        result = self.conn.execute(query)
        while result.has_next():
            user, approver_roles, submitter_roles = result.get_next()
            print(f"  {user}: 承認役 {approver_roles} + 申請役 {submitter_roles}")

    def example_5_permission_analysis(self, user_id: str):
        """例5: 権限分析 - なぜアクセスできるかを完全に説明"""
        print("\n=== 権限分析 ===")
        
        # RDBでは権限の理由を追跡するのが困難
        # KuzuDBではパス全体を取得可能
        query = """
        MATCH (u:User {id: $user_id})
        MATCH path = (u)-[*1..5]->(p:Permission)
        WHERE ALL(rel IN relationships(path) 
                  WHERE type(rel) IN ['HAS_ROLE', 'INHERITS', 'CAN_PERFORM', 
                                      'HAS_TEMPORARY_PERMISSION', 'DELEGATES_TO'])
        
        WITH path, p,
             [node IN nodes(path) | 
                 CASE 
                     WHEN node:User THEN 'User:' + node.name
                     WHEN node:Role THEN 'Role:' + node.name
                     WHEN node:Permission THEN 'Permission:' + node.action + ':' + node.resource
                     ELSE labels(node)[0] + ':' + node.id
                 END
             ] AS path_description
        
        RETURN p.resource, p.action, path_description
        LIMIT 10
        """
        
        print(f"ユーザー {user_id} の権限パス:")
        result = self.conn.execute(query, {"user_id": user_id})
        while result.has_next():
            resource, action, path_desc = result.get_next()
            print(f"\n  {resource}:{action}")
            print(f"  パス: {' → '.join(path_desc)}")

    def example_6_dynamic_permissions(self):
        """例6: 動的権限 - 時間/条件ベースの権限"""
        print("\n=== 動的権限 ===")
        
        # 営業時間内のみ有効な権限
        query = """
        MATCH (u:User)-[r:HAS_ROLE_WITH_SCHEDULE]->(:Role)
        WHERE r.valid_days CONTAINS $today
          AND time() >= r.start_time 
          AND time() <= r.end_time
        RETURN u.name, r.valid_days, r.start_time, r.end_time
        """
        
        # プロジェクト期間中のみ有効な権限
        query2 = """
        MATCH (u:User)-[:ASSIGNED_TO]->(proj:Project)
        WHERE proj.start_date <= date() <= proj.end_date
        MATCH (proj)-[:GRANTS_PERMISSION]->(p:Permission)
        RETURN u.name, proj.name, p.resource, p.action, proj.end_date
        """


# デモ実行
if __name__ == "__main__":
    rbac = ComplexRBACSystem("./complex_rbac.db")
    
    # 各種の複雑な認可パターンをデモ
    rbac.example_1_hierarchical_roles()
    rbac.example_2_context_based_access("user_001", "resource_001")
    rbac.example_3_delegation_chain("user_ceo", "user_intern")
    rbac.example_4_conflict_detection()
    rbac.example_5_permission_analysis("user_001")
    rbac.example_6_dynamic_permissions()