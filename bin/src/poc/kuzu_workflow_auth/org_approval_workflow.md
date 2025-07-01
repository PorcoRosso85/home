# KuzuDB組織承認ワークフロー実装ガイド

## 実装の簡単さ評価: ⭐⭐⭐⭐☆ (簡単)

組織の承認フローとして見ると、KuzuDBは非常に適しています。

## なぜ簡単か

### 1. グラフ構造が組織階層に最適
```cypher
// 組織構造をそのまま表現
(部長)-[:MANAGES]->(課長)-[:MANAGES]->(担当者)
(要件)-[:SUBMITTED_BY]->(担当者)
(要件)-[:REQUIRES_APPROVAL_FROM]->(課長)
(要件)-[:APPROVED_BY]->(課長)
```

### 2. 承認ルートの可視化が容易
```cypher
// 承認経路を簡単に取得
MATCH path = (req:Requirement)-[:SUBMITTED_BY]->()-[:REPORTS_TO*1..3]->(approver)
RETURN path
```

### 3. 既存の要件管理と自然に統合
- すでにステータス管理がある
- バージョン履歴で承認履歴を追跡可能
- LocationURIで部門別管理が可能

## 最小実装プラン（1週間）

### Day 1-2: 組織構造の追加
```cypher
CREATE NODE TABLE Organization (
    id STRING PRIMARY KEY,
    name STRING,
    type STRING  -- 'department', 'team', 'group'
);

CREATE NODE TABLE Employee (
    id STRING PRIMARY KEY,
    name STRING,
    email STRING,
    role STRING  -- '部長', '課長', '担当者'
);

CREATE REL TABLE BELONGS_TO (
    FROM Employee TO Organization
);

CREATE REL TABLE REPORTS_TO (
    FROM Employee TO Employee
);
```

### Day 3-4: 承認フローの実装
```cypher
CREATE NODE TABLE ApprovalFlow (
    id STRING PRIMARY KEY,
    name STRING,
    rules STRING  -- JSON: 承認ルール
);

CREATE REL TABLE REQUIRES_APPROVAL (
    FROM RequirementEntity TO Employee,
    level INT64,  -- 承認レベル (1: 課長, 2: 部長)
    status STRING,  -- 'pending', 'approved', 'rejected'
    comment STRING,
    decided_at STRING
);
```

### Day 5: 承認ロジック
```python
class ApprovalWorkflow:
    def submit_for_approval(self, req_id: str, submitter_id: str):
        """要件を承認申請"""
        # 提出者の上司を自動的に承認者に設定
        query = """
        MATCH (req:RequirementEntity {id: $req_id})
        MATCH (submitter:Employee {id: $submitter_id})
        MATCH (submitter)-[:REPORTS_TO]->(approver:Employee)
        CREATE (req)-[:REQUIRES_APPROVAL {
            level: 1,
            status: 'pending',
            comment: null,
            decided_at: null
        }]->(approver)
        SET req.status = 'pending_approval'
        """
        
    def approve(self, req_id: str, approver_id: str, comment: str = None):
        """要件を承認"""
        query = """
        MATCH (req:RequirementEntity {id: $req_id})
        MATCH (req)-[r:REQUIRES_APPROVAL {status: 'pending'}]->(approver:Employee {id: $approver_id})
        SET r.status = 'approved',
            r.comment = $comment,
            r.decided_at = $timestamp
        SET req.status = 'approved'
        """
        
    def get_pending_approvals(self, approver_id: str):
        """承認待ち一覧を取得"""
        query = """
        MATCH (req:RequirementEntity)-[r:REQUIRES_APPROVAL {status: 'pending'}]->(approver:Employee {id: $approver_id})
        MATCH (req)-[:SUBMITTED_BY]->(submitter:Employee)
        RETURN req.id, req.title, submitter.name, req.created_at
        ORDER BY req.created_at
        """
```

## 実用的な承認パターン

### 1. 階層承認
```python
# 金額や重要度による多段階承認
def create_hierarchical_approval(req_id: str, importance: str):
    if importance == "high":
        # 課長 → 部長 → 役員
        levels = [1, 2, 3]
    else:
        # 課長のみ
        levels = [1]
```

### 2. 並行承認
```python
# 複数部門の承認が必要
def create_parallel_approval(req_id: str, departments: List[str]):
    """関連部門全ての承認が必要"""
    for dept in departments:
        # 各部門の承認者を設定
        create_approval_for_department(req_id, dept)
```

### 3. 条件付き承認
```python
# 条件によって承認者が変わる
def create_conditional_approval(req_id: str, req_type: str):
    if req_type == "システム変更":
        approver = "システム部長"
    elif req_type == "予算関連":
        approver = "経理部長"
```

## 既存システムとの統合例

```python
# 既存のRequirementRepositoryを拡張
class WorkflowRequirementRepository(RequirementRepository):
    def create_requirement(self, req_data: dict, submitter_id: str):
        # 要件作成
        req_id = super().create_requirement(req_data)
        
        # 自動的に承認フローを開始
        self.workflow.submit_for_approval(req_id, submitter_id)
        
        return req_id
    
    def get_dashboard_data(self, employee_id: str):
        """ダッシュボード用データ取得"""
        return {
            "my_submissions": self.get_my_submissions(employee_id),
            "pending_approvals": self.get_pending_approvals(employee_id),
            "approved_recently": self.get_recent_approvals(employee_id)
        }
```

## UI統合イメージ

```python
# FastAPI エンドポイント例
@app.get("/requirements/{req_id}/approval-status")
def get_approval_status(req_id: str):
    """承認状況を取得"""
    query = """
    MATCH (req:RequirementEntity {id: $req_id})
    OPTIONAL MATCH (req)-[r:REQUIRES_APPROVAL]->(approver:Employee)
    RETURN {
        requirement: req,
        approvals: collect({
            approver: approver.name,
            status: r.status,
            comment: r.comment,
            decided_at: r.decided_at
        })
    }
    """

@app.post("/requirements/{req_id}/approve")
def approve_requirement(req_id: str, approver_id: str, decision: str, comment: str = None):
    """承認/却下"""
    if decision == "approve":
        workflow.approve(req_id, approver_id, comment)
    else:
        workflow.reject(req_id, approver_id, comment)
```

## メリット

1. **可視性**: 承認フローが一目でわかる
2. **柔軟性**: 組織変更に簡単に対応
3. **追跡性**: 承認履歴が完全に残る
4. **自動化**: 承認ルールを簡単に実装

## まとめ

組織の承認フローとしてのKuzuDB実装は**非常に簡単**です：
- グラフ構造が組織階層を自然に表現
- 既存の要件管理システムに1週間で統合可能
- 複雑な承認パターンも直感的に実装可能