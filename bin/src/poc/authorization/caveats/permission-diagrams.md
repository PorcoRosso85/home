# SpiceDB 権限付与関連図 (ASCII)

## 1. ドキュメント管理システム

```
┌─────────────────────┐
│   Organization      │
│  ┌─────────────┐   │
│  │ member: alice │   │
│  │ admin: bob   │   │
│  └─────────────┘   │
└──────────┬──────────┘
           │ member権限の伝播
           ▼
┌─────────────────────┐         ┌─────────────────────┐
│   Folder: root      │────────▶│  Folder: projects   │
│  ┌─────────────┐   │ parent  │  ┌─────────────┐   │
│  │owner: org#mem│   │         │  │ 継承: view   │   │
│  └─────────────┘   │         │  │ 継承: edit   │   │
└─────────────────────┘         │  │ 継承: delete │   │
                                │  └─────────────┘   │
                                └──────────┬──────────┘
                                           │ parent
                                           ▼
                                ┌─────────────────────┐
                                │ Folder: project-x   │
                                │  ┌─────────────┐   │
                                │  │ 継承: view   │   │
                                │  │ 継承: edit   │   │
                                │  │ 継承: delete │   │
                                │  └─────────────┘   │
                                └──────────┬──────────┘
                                           │ parent
                                           ▼
                                ┌─────────────────────┐
                                │  Document: spec     │
                                │  ┌─────────────┐   │
                                │  │editor:charlie│   │
                                │  │ 継承: view   │   │
                                │  │ 継承: edit   │   │
                                │  └─────────────┘   │
                                └─────────────────────┘

権限の流れ:
- alice (org member) → root folder → projects → project-x → spec (view権限)
- charlie (direct editor) → spec (edit権限)
```

## 2. GitHub風リポジトリ権限

```
┌─────────────────┐      ┌─────────────────┐
│     Team        │      │  Organization   │
│ ┌────────────┐  │      │ ┌────────────┐  │
│ │member:alice│  │─────▶│ │member:team │  │
│ │lead: bob   │  │      │ │owner: dave │  │
│ └────────────┘  │      │ └────────────┘  │
└─────────────────┘      └────────┬────────┘
                                  │
                                  │ org関係
                                  ▼
┌──────────────────────────────────────────────┐
│              Repository                      │
│ ┌──────────────────────────────────────┐    │
│ │ owner: dave                          │    │
│ │ maintainer: bob                      │    │
│ │ contributor: alice                   │    │
│ │ reader: public                       │    │
│ │                                      │    │
│ │ Permissions:                         │    │
│ │ - read: reader + contributor +       │    │
│ │         maintainer + owner + org→member │    │
│ │ - write: contributor + maintainer + owner │    │
│ │ - admin: maintainer + owner          │    │
│ │ - delete: owner                      │    │
│ └──────────────────────────────────────┘    │
└─────────────────────┬────────────────────────┘
                      │ repo関係
                      ▼
         ┌────────────────────────┐
         │        Issue           │
         │ ┌────────────────────┐ │
         │ │ author: alice      │ │
         │ │ assignee: bob      │ │
         │ │                    │ │
         │ │ Permissions:       │ │
         │ │ - view: repo→read  │ │
         │ │ - edit: author +   │ │
         │ │         repo→write │ │
         │ │ - close: author +  │ │
         │ │          assignee +│ │
         │ │          repo→write│ │
         │ └────────────────────┘ │
         └────────────────────────┘
```

## 3. SaaSマルチテナント権限

```
┌─────────────────────────┐
│        Tenant           │
│ ┌─────────────────────┐ │
│ │ owner: ceo          │ │
│ │ admin: cto          │ │
│ │ member: dev1, dev2  │ │
│ │                     │ │
│ │ Permissions:        │ │
│ │ - invite_users:     │ │
│ │   admin + owner     │ │
│ │ - manage_billing:   │ │
│ │   owner             │ │
│ └─────────────────────┘ │
└────────────┬────────────┘
             │ tenant関係
             ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│       Project A         │         │       Project B         │
│ ┌─────────────────────┐ │         │ ┌─────────────────────┐ │
│ │ manager: pm1        │ │         │ │ manager: pm2        │ │
│ │ developer: dev1     │ │         │ │ developer: dev2     │ │
│ │ viewer: intern1     │ │         │ │ viewer: client1     │ │
│ │                     │ │         │ │                     │ │
│ │ Permissions:        │ │         │ │ Permissions:        │ │
│ │ - view: viewer +    │ │         │ │ - view: viewer +    │ │
│ │         developer + │ │         │ │         developer + │ │
│ │         manager +   │ │         │ │         manager +   │ │
│ │         tenant→member│ │         │ │         tenant→member│ │
│ │ - deploy: developer+│ │         │ │ - configure:        │ │
│ │           manager   │ │         │ │   manager +         │ │
│ └─────────────────────┘ │         │ │   tenant→admin      │ │
└────────────┬────────────┘         │ └─────────────────────┘ │
             │                      └─────────────────────────┘
             │ project関係
             ▼
┌─────────────────────────┐
│       API Key           │
│ ┌─────────────────────┐ │
│ │ creator: dev1       │ │
│ │                     │ │
│ │ Permissions:        │ │
│ │ - use:              │ │
│ │   project→developer │ │
│ │ - rotate/delete:    │ │
│ │   creator +         │ │
│ │   project→manager   │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

## 4. Caveats（条件付き権限）

### 4.1 時間制限付きアクセス

```
┌─────────────────────────────────────────────┐
│              Document                       │
│                                             │
│  viewer: alice [caveat: expiry_caveat]      │
│    ├─ current_time < expiry_time            │
│    └─ expiry_time: "2024-12-31T23:59:59Z"  │
│                                             │
│  owner: bob [no caveat]                    │
│    └─ 無条件でアクセス可能                 │
└─────────────────────────────────────────────┘

時系列での権限変化:
2024-12-30: alice ✓ (view可能), bob ✓ (view可能)
2025-01-01: alice ✗ (期限切れ), bob ✓ (view可能)
```

### 4.2 IPアドレス制限

```
┌─────────────────────────────────────────────┐
│           Secure Resource                   │
│                                             │
│  accessor: alice [caveat: ip_allowlist]     │
│    ├─ request_ip.in_range(allowed_range)    │
│    └─ allowed_range: "10.0.0.0/8"           │
│                                             │
│  リクエスト元による権限判定:               │
│  ┌─────────────┐    ┌─────────────┐       │
│  │ 10.0.1.5    │ ✓  │ 192.168.1.1 │ ✗     │
│  │ (社内IP)    │    │ (外部IP)    │       │
│  └─────────────┘    └─────────────┘       │
└─────────────────────────────────────────────┘
```

### 4.3 承認ワークフロー

```
┌─────────────────────────────────────────────┐
│           Expense Report                    │
│                                             │
│  submitter: employee                        │
│                                             │
│  approver: manager [caveat: approval_limit] │
│    ├─ amount <= threshold                   │
│    └─ threshold: 1000.00                    │
│                                             │
│  approver: director [caveat: approval_limit]│
│    ├─ amount <= threshold                   │
│    └─ threshold: 10000.00                   │
│                                             │
│  finance_team: accountant                   │
└─────────────────────────────────────────────┘

承認フロー:
$500の経費  → manager ✓, director ✓, accountant ✓
$5000の経費 → manager ✗, director ✓, accountant ✓
$15000の経費 → manager ✗, director ✗, accountant ✓ (要上位承認)
```

## 5. 権限の合成パターン

### 5.1 直接権限 + 継承権限

```
         ┌──────────────┐
         │ Folder: root │
         │ viewer: team │
         └──────┬───────┘
                │ parent (継承)
                ▼
         ┌──────────────┐
         │ Document     │
         │ viewer: user │ ← 直接権限
         │ + inherited  │ ← 継承権限
         └──────────────┘

結果: user (直接) + team (継承) = 両方がview可能
```

### 5.2 組織階層での権限伝播

```
┌────────────┐    member of    ┌─────────────┐
│    User    │ ───────────────▶│    Team     │
│   alice    │                  │ engineering │
└────────────┘                  └──────┬──────┘
                                       │ member of
                                       ▼
                                ┌─────────────┐    has access    ┌──────────┐
                                │    Org      │ ────────────────▶│ Resource │
                                │   acme      │                  │  server  │
                                └─────────────┘                  └──────────┘

権限の流れ: alice → engineering team → acme org → server access
```

### 5.3 複合条件での権限判定

```
┌─────────────────────────────────────────────────┐
│                  Request Context                │
│ ┌─────────────────────────────────────────────┐ │
│ │ User: alice                                 │ │
│ │ Time: 2024-12-15T10:00:00Z                 │ │
│ │ IP: 10.0.1.100                             │ │
│ │ Amount: $750                               │ │
│ └─────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────┘
                     │ 評価
                     ▼
┌─────────────────────────────────────────────────┐
│              Permission Check                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✓ User is team member                       │ │
│ │ ✓ Current time < expiry (2024-12-31)       │ │
│ │ ✓ IP is in allowed range (10.0.0.0/8)      │ │
│ │ ✓ Amount ($750) < threshold ($1000)        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Result: PERMISSION GRANTED ✓                    │
└─────────────────────────────────────────────────┘
```

これらの図は、SpiceDBでの権限付与の関係性と、条件付き権限（Caveats）がどのように機能するかを視覚的に示しています。