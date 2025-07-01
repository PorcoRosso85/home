"""
KuzuDB組織承認ワークフローPOC - シンプルな実装例
"""

import kuzu
from datetime import datetime
from typing import List, Dict, Optional


class OrganizationApprovalSystem:
    """組織承認ワークフローシステム"""
    
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """組織承認用のスキーマを初期化"""
        queries = [
            # 組織テーブル
            """CREATE NODE TABLE IF NOT EXISTS Organization (
                id STRING PRIMARY KEY,
                name STRING,
                type STRING
            )""",
            
            # 従業員テーブル
            """CREATE NODE TABLE IF NOT EXISTS Employee (
                id STRING PRIMARY KEY,
                name STRING,
                email STRING,
                role STRING,
                department STRING
            )""",
            
            # 承認フロー定義
            """CREATE NODE TABLE IF NOT EXISTS ApprovalRule (
                id STRING PRIMARY KEY,
                name STRING,
                req_type STRING,
                min_amount INT64,
                max_amount INT64,
                approval_levels STRING
            )""",
            
            # リレーションシップ
            """CREATE REL TABLE IF NOT EXISTS BELONGS_TO (
                FROM Employee TO Organization
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS REPORTS_TO (
                FROM Employee TO Employee
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS SUBMITTED_BY (
                FROM RequirementEntity TO Employee
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS REQUIRES_APPROVAL (
                FROM RequirementEntity TO Employee,
                level INT64,
                status STRING,
                comment STRING,
                decided_at STRING
            )"""
        ]
        
        for query in queries:
            try:
                self.conn.execute(query)
            except:
                pass  # テーブルが既に存在する場合
    
    def setup_organization(self):
        """組織構造のサンプルセットアップ"""
        # 組織作成
        orgs = [
            ("org_dev", "開発部", "department"),
            ("org_qa", "品質保証部", "department"),
            ("org_pm", "企画部", "department")
        ]
        
        for org_id, name, org_type in orgs:
            self.conn.execute(
                "CREATE (o:Organization {id: $id, name: $name, type: $type})",
                {"id": org_id, "name": name, "type": org_type}
            )
        
        # 従業員作成
        employees = [
            ("emp_001", "山田部長", "yamada@example.com", "部長", "開発部"),
            ("emp_002", "鈴木課長", "suzuki@example.com", "課長", "開発部"),
            ("emp_003", "田中担当", "tanaka@example.com", "担当者", "開発部"),
            ("emp_004", "佐藤担当", "sato@example.com", "担当者", "開発部"),
        ]
        
        for emp_id, name, email, role, dept in employees:
            self.conn.execute(
                """CREATE (e:Employee {
                    id: $id, name: $name, email: $email, 
                    role: $role, department: $dept
                })""",
                {"id": emp_id, "name": name, "email": email, 
                 "role": role, "dept": dept}
            )
        
        # 組織階層設定
        hierarchy = [
            ("emp_003", "emp_002"),  # 田中 → 鈴木課長
            ("emp_004", "emp_002"),  # 佐藤 → 鈴木課長
            ("emp_002", "emp_001"),  # 鈴木課長 → 山田部長
        ]
        
        for subordinate, supervisor in hierarchy:
            self.conn.execute(
                """MATCH (sub:Employee {id: $sub_id})
                   MATCH (sup:Employee {id: $sup_id})
                   CREATE (sub)-[:REPORTS_TO]->(sup)""",
                {"sub_id": subordinate, "sup_id": supervisor}
            )
    
    def submit_requirement(self, req_id: str, submitter_id: str, 
                         req_type: str = "standard") -> bool:
        """要件を承認申請"""
        # 要件と提出者を関連付け
        self.conn.execute(
            """MATCH (req:RequirementEntity {id: $req_id})
               MATCH (emp:Employee {id: $emp_id})
               CREATE (req)-[:SUBMITTED_BY]->(emp)
               SET req.status = 'pending_approval'""",
            {"req_id": req_id, "emp_id": submitter_id}
        )
        
        # 承認者を自動設定（直属の上司）
        result = self.conn.execute(
            """MATCH (emp:Employee {id: $emp_id})-[:REPORTS_TO]->(supervisor:Employee)
               RETURN supervisor.id""",
            {"emp_id": submitter_id}
        ).get_next()
        
        if result:
            supervisor_id = result[0]
            self.conn.execute(
                """MATCH (req:RequirementEntity {id: $req_id})
                   MATCH (sup:Employee {id: $sup_id})
                   CREATE (req)-[:REQUIRES_APPROVAL {
                       level: 1,
                       status: 'pending',
                       comment: null,
                       decided_at: null
                   }]->(sup)""",
                {"req_id": req_id, "sup_id": supervisor_id}
            )
            
            # 高優先度の場合は部長承認も必要
            if req_type == "high_priority":
                self._add_higher_approval(req_id, supervisor_id)
            
            return True
        
        return False
    
    def _add_higher_approval(self, req_id: str, current_approver_id: str):
        """上位承認者を追加"""
        result = self.conn.execute(
            """MATCH (emp:Employee {id: $emp_id})-[:REPORTS_TO]->(higher:Employee)
               WHERE higher.role = '部長'
               RETURN higher.id""",
            {"emp_id": current_approver_id}
        ).get_next()
        
        if result:
            higher_id = result[0]
            self.conn.execute(
                """MATCH (req:RequirementEntity {id: $req_id})
                   MATCH (approver:Employee {id: $approver_id})
                   CREATE (req)-[:REQUIRES_APPROVAL {
                       level: 2,
                       status: 'waiting',  -- 前の承認待ち
                       comment: null,
                       decided_at: null
                   }]->(approver)""",
                {"req_id": req_id, "approver_id": higher_id}
            )
    
    def get_pending_approvals(self, approver_id: str) -> List[Dict]:
        """承認待ち一覧を取得"""
        query = """
        MATCH (req:RequirementEntity)-[approval:REQUIRES_APPROVAL {status: 'pending'}]
              ->(approver:Employee {id: $approver_id})
        MATCH (req)-[:SUBMITTED_BY]->(submitter:Employee)
        RETURN req.id, req.title, req.status, submitter.name, 
               approval.level, req.created_at
        ORDER BY req.created_at DESC
        """
        
        results = []
        result_set = self.conn.execute(query, {"approver_id": approver_id})
        while result_set.has_next():
            row = result_set.get_next()
            results.append({
                "req_id": row[0],
                "title": row[1],
                "status": row[2],
                "submitter": row[3],
                "approval_level": row[4],
                "created_at": row[5]
            })
        
        return results
    
    def approve(self, req_id: str, approver_id: str, 
                comment: str = "承認しました") -> bool:
        """要件を承認"""
        # 現在の承認を更新
        self.conn.execute(
            """MATCH (req:RequirementEntity {id: $req_id})
                     -[r:REQUIRES_APPROVAL {status: 'pending'}]->
                     (approver:Employee {id: $approver_id})
               SET r.status = 'approved',
                   r.comment = $comment,
                   r.decided_at = $timestamp""",
            {"req_id": req_id, "approver_id": approver_id, 
             "comment": comment, "timestamp": datetime.now().isoformat()}
        )
        
        # 次のレベルの承認を有効化
        self.conn.execute(
            """MATCH (req:RequirementEntity {id: $req_id})
                     -[r:REQUIRES_APPROVAL {status: 'waiting'}]->()
               SET r.status = 'pending'
               RETURN r""",
            {"req_id": req_id}
        )
        
        # 全ての承認が完了したか確認
        pending = self.conn.execute(
            """MATCH (req:RequirementEntity {id: $req_id})
                     -[r:REQUIRES_APPROVAL]->()
               WHERE r.status IN ['pending', 'waiting']
               RETURN count(r)""",
            {"req_id": req_id}
        ).get_next()[0]
        
        if pending == 0:
            # 全承認完了
            self.conn.execute(
                """MATCH (req:RequirementEntity {id: $req_id})
                   SET req.status = 'approved'""",
                {"req_id": req_id}
            )
        
        return True
    
    def reject(self, req_id: str, approver_id: str, 
               reason: str = "要件の見直しが必要") -> bool:
        """要件を却下"""
        self.conn.execute(
            """MATCH (req:RequirementEntity {id: $req_id})
                     -[r:REQUIRES_APPROVAL {status: 'pending'}]->
                     (approver:Employee {id: $approver_id})
               SET r.status = 'rejected',
                   r.comment = $reason,
                   r.decided_at = $timestamp
               SET req.status = 'rejected'""",
            {"req_id": req_id, "approver_id": approver_id, 
             "reason": reason, "timestamp": datetime.now().isoformat()}
        )
        
        return True
    
    def get_approval_history(self, req_id: str) -> List[Dict]:
        """承認履歴を取得"""
        query = """
        MATCH (req:RequirementEntity {id: $req_id})
        OPTIONAL MATCH (req)-[approval:REQUIRES_APPROVAL]->(approver:Employee)
        RETURN approver.name, approver.role, approval.status, 
               approval.comment, approval.decided_at, approval.level
        ORDER BY approval.level
        """
        
        results = []
        result_set = self.conn.execute(query, {"req_id": req_id})
        while result_set.has_next():
            row = result_set.get_next()
            results.append({
                "approver_name": row[0],
                "approver_role": row[1],
                "status": row[2],
                "comment": row[3],
                "decided_at": row[4],
                "level": row[5]
            })
        
        return results
    
    def get_organization_chart(self, dept: str = None) -> str:
        """組織図を取得（承認経路の可視化）"""
        query = """
        MATCH (emp:Employee)
        WHERE $dept IS NULL OR emp.department = $dept
        OPTIONAL MATCH (emp)-[:REPORTS_TO]->(supervisor:Employee)
        RETURN emp.name, emp.role, supervisor.name
        ORDER BY emp.role DESC
        """
        
        result_set = self.conn.execute(query, {"dept": dept})
        
        chart = "組織承認フロー:\n"
        while result_set.has_next():
            row = result_set.get_next()
            emp_name, role, supervisor = row
            if supervisor:
                chart += f"  {emp_name}({role}) → {supervisor}\n"
            else:
                chart += f"  {emp_name}({role}) [最終承認者]\n"
        
        return chart


# 使用例
if __name__ == "__main__":
    # システム初期化
    approval_system = OrganizationApprovalSystem("./approval_poc.db")
    
    # 組織構造セットアップ
    approval_system.setup_organization()
    
    # 組織図表示
    print(approval_system.get_organization_chart())
    
    # 要件提出の例
    print("\n=== 承認フロー例 ===")
    
    # 1. 田中さんが要件を提出
    req_id = "req_001"
    approval_system.submit_requirement(req_id, "emp_003", "standard")
    print(f"田中担当が要件 {req_id} を提出 → 鈴木課長の承認待ち")
    
    # 2. 鈴木課長の承認待ちリスト
    pending = approval_system.get_pending_approvals("emp_002")
    print(f"\n鈴木課長の承認待ち: {len(pending)}件")
    
    # 3. 鈴木課長が承認
    approval_system.approve(req_id, "emp_002", "問題ありません")
    print("鈴木課長が承認 → 完了")
    
    # 4. 承認履歴確認
    history = approval_system.get_approval_history(req_id)
    print(f"\n承認履歴:")
    for h in history:
        print(f"  - {h['approver_name']}({h['approver_role']}): {h['status']}")
    
    # 高優先度要件の例
    req_id_high = "req_002"
    approval_system.submit_requirement(req_id_high, "emp_004", "high_priority")
    print(f"\n佐藤担当が高優先度要件 {req_id_high} を提出 → 多段階承認フロー開始")