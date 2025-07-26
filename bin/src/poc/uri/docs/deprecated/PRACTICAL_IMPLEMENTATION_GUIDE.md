# 実践的実装ガイド：要求URIシステムの構築

## はじめに

このガイドでは、5層トレーサビリティモデルを実際のプロジェクトで実装する方法を説明します。

## 実装ステップ

### Step 1: ガバナンス体制の確立（1-2週間）

#### 1.1 URI設計規約の策定

```yaml
# uri-design-rules.yaml
naming:
  case: kebab-case
  language: english
  max-length: 60
  
hierarchy:
  levels:
    - capabilities    # L0
    - features       # L1
    - standards      # L2
    - requirements   # L3
    - resources      # L4
    
versioning:
  format: "@v{major}.{minor}"
  example: "req://features/authentication@v2.1"
```

#### 1.2 レビューボードの設置

- アーキテクト（技術面）
- ドメインエキスパート（業務面）
- セキュリティ担当（規制面）

#### 1.3 管理ツールの選定

```python
# GitHubリポジトリでの管理例
uri-registry/
├── capabilities/       # L0
├── features/          # L1
├── standards/         # L2
├── requirements/      # L3
├── implementations/   # L4
└── governance/
    ├── rules.yaml
    └── review-log.md
```

### Step 2: Level 0-1の定義（2-3週間）

#### 2.1 ビジネス能力の洗い出し

```python
# capabilities/customer-management.yaml
uri: req://capabilities/customer-management
name: Customer Management
description: 顧客情報の管理と顧客関係の維持
owner: business-team
features:
  - req://features/customer-registration
  - req://features/customer-profile
  - req://features/customer-analytics
```

#### 2.2 機能への分解

```python
# features/customer-registration.yaml
uri: req://features/customer-registration
name: Customer Registration
capability: req://capabilities/customer-management
standards:
  - req://standards/iso27001/A.9.2
  - req://standards/gdpr/article-7
```

### Step 3: Level 2-3の要求定義（3-4週間）

#### 3.1 標準の選定とマッピング

```python
# Well-Architected Frameworkの例
def map_waf_to_features():
    mappings = {
        "req://waf/security/identity": [
            "req://features/user-authentication",
            "req://features/access-control",
            "req://features/credential-management"
        ],
        "req://waf/reliability/backup": [
            "req://features/data-backup",
            "req://features/disaster-recovery"
        ]
    }
    return mappings
```

#### 3.2 具体的要求の文書化

```yaml
# requirements/enforce-mfa.yaml
uri: req://requirements/enforce-mfa-privileged
name: Enforce MFA for Privileged Users
category: req://standards/waf/security/identity
description: |
  特権ユーザーには必ず多要素認証を強制する
test_criteria:
  - 特権ユーザーがMFAなしでログインできないこと
  - MFA設定が90日ごとに見直されること
priority: critical
```

### Step 4: 実装との連携（継続的）

#### 4.1 Infrastructure as Codeでの参照

```hcl
# Terraform例
resource "aws_iam_policy" "enforce_mfa" {
  name        = "EnforceMfaPolicy"
  description = "Implements req://requirements/enforce-mfa-privileged"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Deny"
      Action = "*"
      Resource = "*"
      Condition = {
        BoolIfExists = {
          "aws:MultiFactorAuthPresent" = "false"
        }
      }
    }]
  })
  
  tags = {
    requirement_uri = "req://requirements/enforce-mfa-privileged"
    compliance      = "waf-security"
  }
}
```

#### 4.2 実装URIの自動収集

```python
# 実装URIコレクター
import boto3
import json

def collect_implementation_uris():
    """タグから要求URIと実装URIのマッピングを収集"""
    iam = boto3.client('iam')
    mappings = []
    
    # IAMポリシーを検査
    policies = iam.list_policies(Scope='Local')
    for policy in policies['Policies']:
        tags = iam.list_policy_tags(PolicyArn=policy['Arn'])
        for tag in tags['Tags']:
            if tag['Key'] == 'requirement_uri':
                mappings.append({
                    'requirement': tag['Value'],
                    'implementation': policy['Arn'],
                    'type': 'aws:iam:policy'
                })
    
    return mappings
```

### Step 5: 継続的な運用

#### 5.1 定期レビュー（四半期ごと）

```markdown
# レビューチェックリスト
- [ ] 新しいビジネス能力の追加が必要か？
- [ ] 既存機能の統廃合が必要か？
- [ ] 標準の更新に対応しているか？
- [ ] 実装が要求から乖離していないか？
- [ ] 死んだURIは存在しないか？
```

#### 5.2 監査対応

```python
def generate_compliance_report(standard_uri):
    """特定標準に対するコンプライアンスレポート生成"""
    report = {
        'standard': standard_uri,
        'coverage': calculate_coverage(standard_uri),
        'gaps': find_gaps(standard_uri),
        'evidence': collect_evidence(standard_uri)
    }
    return report
```

## ツールとの統合

### GitHub Actions例

```yaml
# .github/workflows/uri-validation.yml
name: URI Validation
on:
  pull_request:
    paths:
      - 'uri-registry/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate URI Structure
        run: |
          python scripts/validate_uris.py
      - name: Check for Duplicates
        run: |
          python scripts/check_duplicates.py
      - name: Verify References
        run: |
          python scripts/verify_references.py
```

### Grafanaダッシュボード例

```json
{
  "dashboard": {
    "title": "Requirement Traceability",
    "panels": [
      {
        "title": "Coverage by Standard",
        "query": "SELECT standard, COUNT(DISTINCT requirement) FROM uri_mappings GROUP BY standard"
      },
      {
        "title": "Implementation Status",
        "query": "SELECT requirement, COUNT(implementation) as impl_count FROM uri_mappings GROUP BY requirement"
      }
    ]
  }
}
```

## ベストプラクティス

### DO ✅

1. **段階的導入**: 全てを一度に実装せず、重要な領域から開始
2. **自動化重視**: 可能な限り自動化し、人的エラーを削減
3. **定期的な棚卸**: 四半期ごとにURIの妥当性を確認
4. **クロスファンクショナル**: 技術・業務・規制の観点を統合

### DON'T ❌

1. **過度な詳細化**: 管理不能になるほど細かくしない
2. **頻繁な変更**: 上位層（L0-L1）は安定させる
3. **機械的なマッピング**: 標準の意図を理解せずに対応付けない
4. **サイロ化**: チーム間で独自のURI体系を作らない

## まとめ

このシステムの成功は、技術的な実装よりも組織的な取り組みにかかっています。適切なガバナンスと継続的な改善により、真のトレーサビリティが実現できます。