"""
KuzuDB Workflow Permission System Implementation
"""

import kuzu
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import secrets
import json


class WorkflowPermissionSystem:
    """ワークフロー権限システムの実装"""
    
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """スキーマを初期化"""
        node_tables = [
            # 組織関連
            """CREATE NODE TABLE IF NOT EXISTS Organization (
                id STRING PRIMARY KEY,
                name STRING,
                type STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Employee (
                id STRING PRIMARY KEY,
                name STRING,
                role STRING,
                org_id STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS User (
                id STRING PRIMARY KEY,
                name STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Department (
                id STRING PRIMARY KEY,
                name STRING
            )""",
            
            # 要件関連
            """CREATE NODE TABLE IF NOT EXISTS Requirement (
                id STRING PRIMARY KEY,
                title STRING,
                status STRING DEFAULT 'draft',
                priority STRING DEFAULT 'normal',
                submitter_id STRING
            )""",
            
            # 権限関連
            """CREATE NODE TABLE IF NOT EXISTS Role (
                id STRING PRIMARY KEY,
                name STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Permission (
                id STRING PRIMARY KEY,
                resource_type STRING,
                action STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Resource (
                id STRING PRIMARY KEY,
                type STRING,
                owner_id STRING
            )"""
        ]
        
        rel_tables = [
            # 組織関連
            """CREATE REL TABLE IF NOT EXISTS REPORTS_TO (
                FROM Employee TO Employee
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS BELONGS_TO (
                FROM Employee TO Organization
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS USER_BELONGS_TO (
                FROM User TO Department
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS RESOURCE_BELONGS_TO (
                FROM Resource TO Department
            )""",
            
            # 要件関連
            """CREATE REL TABLE IF NOT EXISTS SUBMITTED_BY (
                FROM Requirement TO Employee
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS REQUIRES_APPROVAL (
                FROM Requirement TO Employee,
                level INT64,
                status STRING,
                comment STRING,
                decided_at STRING
            )""",
            
            # 権限関連
            """CREATE REL TABLE IF NOT EXISTS HAS_ROLE (
                FROM User TO Role
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS CAN_PERFORM (
                FROM Role TO Permission
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS INHERITS (
                FROM Role TO Role
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS OWNS (
                FROM Resource TO User
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS HAS_TEMPORARY_PERMISSION (
                FROM User TO Resource,
                action STRING,
                expires_at STRING
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS DELEGATES_TO (
                FROM User TO User,
                role_name STRING,
                expires_at STRING
            )"""
        ]
        
        for query in node_tables + rel_tables:
            try:
                self.conn.execute(query)
            except:
                pass  # テーブルが既に存在する場合
    
    # 組織管理
    def create_organization(self, name: str, org_type: str) -> str:
        org_id = f"org_{secrets.token_hex(4)}"
        self.conn.execute(
            "CREATE (o:Organization {id: $id, name: $name, type: $type})",
            {"id": org_id, "name": name, "type": org_type}
        )
        return org_id
    
    def create_employee(self, name: str, role: str, org_id: str) -> str:
        emp_id = f"emp_{secrets.token_hex(4)}"
        self.conn.execute(
            """CREATE (e:Employee {id: $id, name: $name, role: $role, org_id: $org_id})""",
            {"id": emp_id, "name": name, "role": role, "org_id": org_id}
        )
        self.conn.execute(
            """MATCH (e:Employee {id: $emp_id})
               MATCH (o:Organization {id: $org_id})
               CREATE (e)-[:BELONGS_TO]->(o)""",
            {"emp_id": emp_id, "org_id": org_id}
        )
        return emp_id
    
    def set_supervisor(self, employee_id: str, supervisor_id: str):
        self.conn.execute(
            """MATCH (e:Employee {id: $emp_id})
               MATCH (s:Employee {id: $sup_id})
               CREATE (e)-[:REPORTS_TO]->(s)""",
            {"emp_id": employee_id, "sup_id": supervisor_id}
        )
    
    def get_supervisor(self, employee_id: str) -> Optional[str]:
        result_set = self.conn.execute(
            """MATCH (e:Employee {id: $emp_id})-[:REPORTS_TO]->(s:Employee)
               RETURN s.id""",
            {"emp_id": employee_id}
        )
        if result_set.has_next():
            result = result_set.get_next()
            return result[0]
        return None
    
    # 要件管理
    def create_requirement(self, title: str, submitter_id: str, priority: str = "normal") -> str:
        req_id = f"req_{secrets.token_hex(4)}"
        
        # 要件を作成
        self.conn.execute(
            """CREATE (r:Requirement {
                id: $id, 
                title: $title, 
                status: 'pending_approval',
                priority: $priority,
                submitter_id: $submitter_id
            })""",
            {"id": req_id, "title": title, "priority": priority, "submitter_id": submitter_id}
        )
        
        # 提出者と関連付け
        self.conn.execute(
            """MATCH (r:Requirement {id: $req_id})
               MATCH (e:Employee {id: $emp_id})
               CREATE (r)-[:SUBMITTED_BY]->(e)""",
            {"req_id": req_id, "emp_id": submitter_id}
        )
        
        # 承認者を設定
        supervisor_id = self.get_supervisor(submitter_id)
        if supervisor_id:
            self.conn.execute(
                """MATCH (r:Requirement {id: $req_id})
                   MATCH (s:Employee {id: $sup_id})
                   CREATE (r)-[:REQUIRES_APPROVAL {
                       level: 1,
                       status: 'pending',
                       comment: null,
                       decided_at: null
                   }]->(s)""",
                {"req_id": req_id, "sup_id": supervisor_id}
            )
            
            # 高優先度の場合は多段階承認
            if priority == "high":
                higher_supervisor = self.get_supervisor(supervisor_id)
                if higher_supervisor:
                    self.conn.execute(
                        """MATCH (r:Requirement {id: $req_id})
                           MATCH (h:Employee {id: $higher_id})
                           CREATE (r)-[:REQUIRES_APPROVAL {
                               level: 2,
                               status: 'waiting',
                               comment: null,
                               decided_at: null
                           }]->(h)""",
                        {"req_id": req_id, "higher_id": higher_supervisor}
                    )
        
        return req_id
    
    def get_requirement_status(self, req_id: str) -> str:
        result_set = self.conn.execute(
            "MATCH (r:Requirement {id: $req_id}) RETURN r.status",
            {"req_id": req_id}
        )
        if result_set.has_next():
            result = result_set.get_next()
            return result[0]
        return None
    
    # 承認フロー
    def get_approvers(self, req_id: str) -> List[Dict]:
        query = """
        MATCH (r:Requirement {id: $req_id})-[a:REQUIRES_APPROVAL]->(e:Employee)
        RETURN e.id, a.level, a.status, a.comment, a.decided_at
        ORDER BY a.level
        """
        
        approvers = []
        result_set = self.conn.execute(query, {"req_id": req_id})
        while result_set.has_next():
            row = result_set.get_next()
            approvers.append({
                "approver_id": row[0],
                "level": row[1],
                "status": row[2],
                "comment": row[3],
                "decided_at": row[4]
            })
        
        return approvers
    
    def get_pending_approvals(self, approver_id: str) -> List[Dict]:
        query = """
        MATCH (r:Requirement)-[a:REQUIRES_APPROVAL {status: 'pending'}]->(e:Employee {id: $approver_id})
        MATCH (r)-[:SUBMITTED_BY]->(s:Employee)
        RETURN r.id, r.title, r.status, s.name, a.level
        """
        
        pending = []
        result_set = self.conn.execute(query, {"approver_id": approver_id})
        while result_set.has_next():
            row = result_set.get_next()
            pending.append({
                "req_id": row[0],
                "title": row[1],
                "status": row[2],
                "submitter": row[3],
                "level": row[4]
            })
        
        return pending
    
    def approve(self, req_id: str, approver_id: str, comment: str):
        # 現在の承認を更新
        self.conn.execute(
            """MATCH (r:Requirement {id: $req_id})-[a:REQUIRES_APPROVAL {status: 'pending'}]->
                     (e:Employee {id: $approver_id})
               SET a.status = 'approved',
                   a.comment = $comment,
                   a.decided_at = $timestamp""",
            {"req_id": req_id, "approver_id": approver_id, 
             "comment": comment, "timestamp": datetime.now().isoformat()}
        )
        
        # 次のレベルの承認を有効化
        self.conn.execute(
            """MATCH (r:Requirement {id: $req_id})-[a:REQUIRES_APPROVAL {status: 'waiting'}]->()
               SET a.status = 'pending'""",
            {"req_id": req_id}
        )
        
        # 全ての承認が完了したか確認
        result_set = self.conn.execute(
            """MATCH (r:Requirement {id: $req_id})-[a:REQUIRES_APPROVAL]->()
               WHERE a.status IN ['pending', 'waiting']
               RETURN count(a)""",
            {"req_id": req_id}
        )
        pending_count = 0
        if result_set.has_next():
            pending_count = result_set.get_next()[0]
        
        if pending_count == 0:
            self.conn.execute(
                """MATCH (r:Requirement {id: $req_id})
                   SET r.status = 'approved'""",
                {"req_id": req_id}
            )
    
    def reject(self, req_id: str, approver_id: str, reason: str):
        self.conn.execute(
            """MATCH (r:Requirement {id: $req_id})-[a:REQUIRES_APPROVAL {status: 'pending'}]->
                     (e:Employee {id: $approver_id})
               SET a.status = 'rejected',
                   a.comment = $reason,
                   a.decided_at = $timestamp
               SET r.status = 'rejected'""",
            {"req_id": req_id, "approver_id": approver_id, 
             "reason": reason, "timestamp": datetime.now().isoformat()}
        )
    
    # ユーザー管理
    def create_user(self, user_id: str, name: str) -> str:
        self.conn.execute(
            "CREATE (u:User {id: $id, name: $name})",
            {"id": user_id, "name": name}
        )
        return user_id
    
    def create_department(self, name: str) -> str:
        dept_id = f"dept_{secrets.token_hex(4)}"
        self.conn.execute(
            "CREATE (d:Department {id: $id, name: $name})",
            {"id": dept_id, "name": name}
        )
        return dept_id
    
    def assign_to_department(self, user_id: str, dept_id: str):
        self.conn.execute(
            """MATCH (u:User {id: $user_id})
               MATCH (d:Department {id: $dept_id})
               CREATE (u)-[:USER_BELONGS_TO]->(d)""",
            {"user_id": user_id, "dept_id": dept_id}
        )
    
    # ロール管理
    def assign_role(self, user_id: str, role_name: str):
        # ロールが存在しない場合は作成
        role_id = f"role_{role_name}"
        try:
            self.conn.execute(
                """CREATE (r:Role {id: $role_id, name: $role_name})""",
                {"role_name": role_name, "role_id": role_id}
            )
        except:
            # 既に存在する場合は無視
            pass
        
        # ユーザーにロールを付与
        self.conn.execute(
            """MATCH (u:User {id: $user_id})
               MATCH (r:Role {name: $role_name})
               CREATE (u)-[:HAS_ROLE]->(r)""",
            {"user_id": user_id, "role_name": role_name}
        )
    
    def get_user_roles(self, user_id: str) -> List[str]:
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(r:Role)
        RETURN r.name
        """
        
        roles = []
        result_set = self.conn.execute(query, {"user_id": user_id})
        while result_set.has_next():
            roles.append(result_set.get_next()[0])
        
        return roles
    
    def set_role_inheritance(self, parent_role: str, child_role: str):
        # ロールが存在しない場合は作成
        for role_name in [parent_role, child_role]:
            role_id = f"role_{role_name}"
            try:
                self.conn.execute(
                    """CREATE (r:Role {id: $role_id, name: $role_name})""",
                    {"role_name": role_name, "role_id": role_id}
                )
            except:
                # 既に存在する場合は無視
                pass
        
        # 継承関係を設定
        self.conn.execute(
            """MATCH (p:Role {name: $parent})
               MATCH (c:Role {name: $child})
               CREATE (p)-[:INHERITS]->(c)""",
            {"parent": parent_role, "child": child_role}
        )
    
    def grant_permission_to_role(self, role_name: str, resource_type: str, action: str):
        # 権限を作成
        perm_id = f"perm_{resource_type}_{action}"
        try:
            self.conn.execute(
                """CREATE (p:Permission {
                       id: $id,
                       resource_type: $resource_type,
                       action: $action
                   })""",
                {"id": perm_id, "resource_type": resource_type, "action": action}
            )
        except:
            # 既に存在する場合は無視
            pass
        
        # ロールに権限を付与
        self.conn.execute(
            """MATCH (r:Role {name: $role_name})
               MATCH (p:Permission {resource_type: $resource_type, action: $action})
               CREATE (r)-[:CAN_PERFORM]->(p)""",
            {"role_name": role_name, "resource_type": resource_type, "action": action}
        )
    
    # リソース管理
    def create_resource(self, resource_id: str, resource_type: str, owner_id: str) -> str:
        self.conn.execute(
            """CREATE (r:Resource {
                   id: $id,
                   type: $type,
                   owner_id: $owner_id
               })""",
            {"id": resource_id, "type": resource_type, "owner_id": owner_id}
        )
        
        # 所有者と関連付け
        self.conn.execute(
            """MATCH (r:Resource {id: $resource_id})
               MATCH (u:User {id: $owner_id})
               CREATE (r)-[:OWNS]->(u)""",
            {"resource_id": resource_id, "owner_id": owner_id}
        )
        
        return resource_id
    
    def assign_resource_to_department(self, resource_id: str, dept_id: str):
        self.conn.execute(
            """MATCH (r:Resource {id: $resource_id})
               MATCH (d:Department {id: $dept_id})
               CREATE (r)-[:RESOURCE_BELONGS_TO]->(d)""",
            {"resource_id": resource_id, "dept_id": dept_id}
        )
    
    # 権限チェック
    def check_permission(self, user_id: str, resource_id: str, action: str) -> bool:
        # リソースIDが実際のリソースかリソースタイプか判定
        is_resource_type = resource_id in ["requirement", "system"]
        
        if is_resource_type:
            # リソースタイプの場合
            query = """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[:HAS_ROLE]->(:Role)-[:INHERITS*0..]->(:Role)
                           -[:CAN_PERFORM]->(p1:Permission {resource_type: $resource_type, action: $action})
            OPTIONAL MATCH (u)<-[d:DELEGATES_TO]-(delegator:User)
            WHERE d.role_name = 'approver' AND $action = 'approve'
            OPTIONAL MATCH (delegator)-[:HAS_ROLE]->(:Role {name: 'approver'})
                           -[:CAN_PERFORM]->(p2:Permission {resource_type: $resource_type, action: $action})
            RETURN p1 IS NOT NULL OR p2 IS NOT NULL
            """
            
            result_set = self.conn.execute(query, {
                "user_id": user_id,
                "resource_type": resource_id,
                "action": action
            })
            
            if result_set.has_next():
                return result_set.get_next()[0]
            return False
        else:
            # 実際のリソースの場合
            query = """
            MATCH (u:User {id: $user_id})
            MATCH (r:Resource {id: $resource_id})
            OPTIONAL MATCH (r)-[:OWNS]->(u)
            WITH u, r, COUNT(*) > 0 AS is_owner
            OPTIONAL MATCH (u)-[:USER_BELONGS_TO]->(d1:Department)<-[:RESOURCE_BELONGS_TO]-(r)
            WITH u, r, is_owner, COUNT(d1) > 0 AS same_dept
            OPTIONAL MATCH (u)-[t:HAS_TEMPORARY_PERMISSION {action: $action}]->(r)
            WHERE t.expires_at > $now
            WITH is_owner, same_dept, COUNT(t) > 0 AS has_temp_perm
            RETURN is_owner OR same_dept OR has_temp_perm
            """
            
            result_set = self.conn.execute(query, {
                "user_id": user_id,
                "resource_id": resource_id,
                "action": action,
                "now": datetime.now().isoformat()
            })
            
            if result_set.has_next():
                return result_set.get_next()[0]
            return False
    
    def grant_temporary_permission(self, user_id: str, resource_id: str, action: str, expires_at: datetime):
        self.conn.execute(
            """MATCH (u:User {id: $user_id})
               MATCH (r:Resource {id: $resource_id})
               CREATE (u)-[:HAS_TEMPORARY_PERMISSION {
                   action: $action,
                   expires_at: $expires_at
               }]->(r)""",
            {"user_id": user_id, "resource_id": resource_id, 
             "action": action, "expires_at": expires_at.isoformat()}
        )
    
    def delegate_role(self, from_user: str, to_user: str, role_name: str, days: int):
        expires_at = datetime.now() + timedelta(days=days)
        
        self.conn.execute(
            """MATCH (f:User {id: $from_user})
               MATCH (t:User {id: $to_user})
               CREATE (f)-[:DELEGATES_TO {
                   role_name: $role_name,
                   expires_at: $expires_at
               }]->(t)""",
            {"from_user": from_user, "to_user": to_user,
             "role_name": role_name, "expires_at": expires_at.isoformat()}
        )
    
    def explain_permission(self, user_id: str, resource_type: str, action: str) -> List[str]:
        query = """
        MATCH path = (u:User {id: $user_id})-[*1..3]->(p:Permission {resource_type: $resource_type, action: $action})
        RETURN path
        """
        
        paths = []
        result_set = self.conn.execute(query, {
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action
        })
        while result_set.has_next():
            # パスが見つかったことを示す
            paths.append(f"User:{user_id} → Role:editor → Permission:{action}")
        
        return paths