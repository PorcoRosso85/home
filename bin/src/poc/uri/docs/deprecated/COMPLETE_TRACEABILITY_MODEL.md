# 完全なトレーサビリティモデル：5層構造＋ガバナンス

## モデル全体像

```
+=================================================================================+
| G O V E R N A N C E   &   C H A N G E   M A N A G E M E N T                   |
| (参照元: Cloud Vendor's Well-Architected Framework - Public Docs)               |
+=================================================================================+
       ^                  ^                     ^        ^          ^
       |                  |                     |        |          |
       v                  v                     v        v          v
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -+
| Level 0: Business Capability                                                    |
+---------------------------------------------------------------------------------+
| Level 1: Feature (W-AF Pillar / Design Principle)                               |
+---------------------------------------------------------------------------------+
       +------------------------------------+
       | Feature: Identity Management       |
       | (.../features/identity-management) |
       +------------------------------------+
                     | "要求カテゴリを持つ (HAS_REQUIREMENTS_IN)"
+---------------------------------------------------------------------------------+
| Level 2: Classification (W-AF Best Practice / Recommendation)                   |
+---------------------------------------------------------------------------------+
       +------------------------------------+
       | Category: Use Strong Authentication|
       +------------------------------------+
                     | "含む (CONTAINS)"
+---------------------------------------------------------------------------------+
| Level 3: Concrete Requirement (W-AF Checklist Item)                             |
+---------------------------------------------------------------------------------+
       +------------------------------------+
       | Enforce MFA for privileged users.  |
       | (.../waf.../sec.../enforce-mfa)     |
       +------------------------------------+
                     | "実装される (IMPLEMENTED_BY)"
+---------------------------------------------------------------------------------+
| Level 4: Implementation (SDK/API Resource URI)                                  |
+---------------------------------------------------------------------------------+
       +------------------------------------+
       | arn:aws:iam::123456789012:policy/   |
       | EnforceMfaForAdminsPolicy          |
       +------------------------------------+
```

## 各層の詳細

### ガバナンス層（最上位）

**目的**: URI生成と管理の安全性を保証する人間系のプロセス

**構成要素**:
- **URI設計規約**: 命名規則、階層構造のルール
- **URI払い出し台帳**: 全URIの一元管理
- **レビューボード**: 新規URI承認機関
- **ライフサイクル管理**: 廃止・統合プロセス

### Level 0: Business Capability（ビジネス能力）

**目的**: ビジネス視点での機能分類

**例**:
```
req://capabilities/customer-management
req://capabilities/order-processing
req://capabilities/risk-management
```

**特徴**:
- 技術に依存しない
- 長期的に安定
- 経営層も理解可能

### Level 1: Feature（機能・サービス）

**目的**: ドメインまたはサービス単位での機能分割

**例**:
```
req://features/user-authentication
req://features/payment-processing
req://features/data-encryption
```

**参照元候補**:
- Well-Architected Framework のピラー
- Domain-Driven Design のサブドメイン
- マイクロサービスの境界

### Level 2: Classification（分類・カテゴリ）

**目的**: セキュリティ標準や規制要件のカテゴリ分類

**例**:
```
req://waf/security/identity-access-management
req://iso27001/A.9-access-control
req://pci-dss/requirement-8
```

**特徴**:
- 標準文書の章立てに対応
- 監査時の参照が容易
- 複数標準の統合が可能

### Level 3: Concrete Requirement（具体的要求）

**目的**: 実装すべき具体的な要求事項

**例**:
```
req://waf/sec/iam/enforce-mfa-privileged-users
req://waf/sec/iam/rotate-credentials-90days
req://waf/sec/iam/use-temporary-credentials
```

**特徴**:
- 検証可能な粒度
- テストケースに変換可能
- 実装とは独立

### Level 4: Implementation（実装）

**目的**: 実際のクラウドリソースへの参照

**例**:
```
arn:aws:iam::123456789012:policy/EnforceMfaPolicy
arn:aws:lambda:us-east-1:123456789012:function:PasswordRotator
azurerm_policy_definition.enforce_mfa.id
```

**特徴**:
- 環境ごとに異なる
- 頻繁に変更される
- 自動取得可能

## 層間の関係性

### 上から下へ（設計時）
1. ビジネス能力から機能を導出
2. 機能から必要な要求カテゴリを特定
3. カテゴリから具体的要求を列挙
4. 要求を満たす実装を構築

### 下から上へ（監査時）
1. 実装リソースから対応する要求を確認
2. 要求が属するカテゴリを確認
3. カテゴリを支える機能を確認
4. 機能が実現するビジネス能力を確認

## 変更に対する強靭性

### 実装が変更された場合
- Level 4のみ更新
- 上位層は不変
- 新ARNを要求にリンクし直すだけ

### 標準が改訂された場合
- Level 2-3を更新
- Level 0-1は安定
- 影響範囲が明確

### ビジネス要求が変化した場合
- Level 0から見直し
- トップダウンで影響分析
- 計画的な移行が可能

## このモデルの価値

1. **完全性**: ビジネスから実装まで切れ目なく追跡
2. **安定性**: 上位層ほど変更に強い
3. **検証可能性**: 各層で監査・テストが可能
4. **自動化**: Level 4は自動取得、上位は人間の判断
5. **共通言語**: 経営層から開発者まで同じモデルで会話