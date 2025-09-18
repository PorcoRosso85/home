# SpiceDB 権限付与の実装例とユースケース

## 1. ドキュメント管理システム

### スキーマ
```zaml
definition user {}

definition organization {
    relation member: user
    relation admin: user
}

definition folder {
    relation parent: folder
    relation owner: user | organization#member
    relation editor: user | organization#member
    relation viewer: user | organization#member
    
    permission view = viewer + editor + owner + parent->view
    permission edit = editor + owner + parent->edit
    permission delete = owner + parent->delete
}

definition document {
    relation parent: folder
    relation owner: user
    relation editor: user | organization#member
    relation viewer: user | organization#member
    
    permission view = viewer + editor + owner + parent->view
    permission edit = editor + owner + parent->edit
    permission delete = owner + parent->delete
}
```

### 使用例
```bash
# 組織の作成
organization:acme#member@user:alice
organization:acme#admin@user:bob

# フォルダ階層
folder:root#owner@organization:acme#member
folder:projects#parent@folder:root
folder:project-x#parent@folder:projects

# ドキュメント権限
document:spec#parent@folder:project-x
document:spec#editor@user:charlie
```

## 2. GitHub風リポジトリ権限

### スキーマ
```zaml
definition user {}

definition team {
    relation member: user
    relation lead: user
}

definition organization {
    relation member: user | team#member
    relation owner: user | team#member
    
    permission manage_billing = owner
    permission create_repo = member + owner
}

definition repository {
    relation owner: user | team#member
    relation maintainer: user | team#member
    relation contributor: user | team#member
    relation reader: user | team#member
    relation org: organization
    
    permission read = reader + contributor + maintainer + owner + org->member
    permission write = contributor + maintainer + owner
    permission admin = maintainer + owner
    permission delete = owner
}

definition issue {
    relation repo: repository
    relation author: user
    relation assignee: user
    
    permission view = repo->read
    permission comment = repo->read
    permission edit = author + repo->write
    permission close = author + assignee + repo->write
}
```

## 3. SaaSアプリケーションのマルチテナント権限

### スキーマ
```zaml
definition user {}

definition tenant {
    relation owner: user
    relation admin: user
    relation member: user
    
    permission invite_users = admin + owner
    permission manage_billing = owner
    permission view_audit_log = admin + owner
}

definition project {
    relation tenant: tenant
    relation manager: user
    relation developer: user
    relation viewer: user
    
    permission view = viewer + developer + manager + tenant->member
    permission deploy = developer + manager
    permission configure = manager + tenant->admin
}

definition api_key {
    relation project: project
    relation creator: user
    
    permission use = project->developer
    permission rotate = creator + project->manager
    permission delete = creator + project->manager
}
```

## 4. Caveats（条件付き権限）の活用例

### 時間制限付きアクセス
```zaml
definition document {
    relation viewer: user with expiry_caveat
    relation owner: user
    
    permission view = viewer + owner
}

caveat expiry_caveat(current_time timestamp, expiry_time timestamp) {
    current_time < expiry_time
}

// 使用例：2024年12月31日まで有効な閲覧権限
// document:contract#viewer@user:alice[expiry_caveat:{"expiry_time":"2024-12-31T23:59:59Z"}]
```

### IPアドレス制限
```zaml
definition secure_resource {
    relation accessor: user with ip_allowlist_caveat
    
    permission access = accessor
}

caveat ip_allowlist_caveat(request_ip ipaddress, allowed_range string) {
    request_ip.in_range(allowed_range)
}

// 使用例：社内ネットワークからのみアクセス可能
// secure_resource:financial-data#accessor@user:alice[ip_allowlist_caveat:{"allowed_range":"10.0.0.0/8"}]
```

### 承認ワークフロー
```zaml
definition expense_report {
    relation submitter: user
    relation approver: user with approval_caveat
    relation finance_team: user
    
    permission submit = submitter
    permission approve = approver
    permission process = finance_team
}

caveat approval_caveat(amount decimal, threshold decimal) {
    amount <= threshold
}

// 使用例：1000ドル以下の経費は部門長が承認可能
// expense_report:q4-travel#approver@user:dept-manager[approval_caveat:{"threshold":"1000.00"}]
```

## 5. 実装のベストプラクティス

### 1. 最小権限の原則
```zaml
// 悪い例：広すぎる権限
permission admin = user

// 良い例：具体的な権限の組み合わせ
permission admin = manage_users + manage_settings + view_audit_log
```

### 2. 権限の継承を活用
```zaml
// フォルダから権限を継承
permission view = direct_viewer + parent_folder->view
```

### 3. 組織構造の反映
```zaml
// チームや部門の階層を権限に反映
definition department {
    relation parent_dept: department
    relation manager: user
    relation member: user
    
    permission view_budget = manager + parent_dept->manager
}
```

これらの例は、SpiceDBの柔軟な権限モデルを活用して、複雑な認可要件を宣言的に表現する方法を示しています。