# 多段階契約管理システム仕様書

## 契約エンティティ管理

### 概要
契約エンティティ管理は、多段階契約システムの中核となる契約データの構造と管理方法を定義する。DDDのEntityパターンとGraphDBを組み合わせて実装する。

### DDDモデル定義

#### Contract Entity
```python
# domain/model/contract.py
class Contract(Entity):
    """契約エンティティ - ビジネスルールを含む"""
    
    def __init__(
        self,
        contract_id: ContractId,
        contract_type: ContractType,
        parties: List[Party],
        parent_contract: Optional[Contract],
        terms: ContractTerms,
        status: ContractStatus,
        created_at: datetime,
        expires_at: datetime
    ):
        self._id = contract_id
        self._type = contract_type
        self._parties = parties
        self._parent_contract = parent_contract
        self._terms = terms
        self._status = status
        self._created_at = created_at
        self._expires_at = expires_at
        self._validate_business_rules()
    
    def _validate_business_rules(self):
        """ビジネスルールの検証"""
        # 親契約の有効性チェック
        # 契約期間の妥当性チェック
        # 当事者の資格チェック
        pass
```

#### Value Objects
```python
class ContractType(Enum):
    RESELLER = "reseller"          # 代理店契約
    REFERRAL = "referral"          # 紹介契約
    COMMUNITY = "community"        # コミュニティ契約
    VALUE_CHAIN = "value_chain"    # バリューチェーン契約

class ContractStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
```

### GraphDB スキーマ定義 (Kuzu DDL)

#### ノード定義
```sql
-- 契約ノード
CREATE NODE TABLE Contract(
    id STRING PRIMARY KEY,
    type STRING NOT NULL,
    status STRING NOT NULL,
    terms JSON,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 契約当事者ノード
CREATE NODE TABLE Party(
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    type STRING NOT NULL,  -- 'company', 'individual'
    tax_id STRING,
    created_at TIMESTAMP NOT NULL
);
```

#### エッジ定義
```sql
-- 契約の親子関係
CREATE REL TABLE ParentContract(
    FROM Contract TO Contract,
    inheritance_type STRING,      -- 'full', 'partial', 'none'
    inherited_terms JSON,
    created_at TIMESTAMP
);

-- 契約と当事者の関係
CREATE REL TABLE ContractParty(
    FROM Contract TO Party,
    role STRING NOT NULL,         -- 'buyer', 'seller', 'referrer', 'guarantor'
    commission_rate DOUBLE,
    special_terms JSON,
    joined_at TIMESTAMP NOT NULL
);

-- 当事者間の紹介関係
CREATE REL TABLE ReferralChain(
    FROM Party TO Party,
    contract_id STRING NOT NULL,
    referral_date TIMESTAMP NOT NULL,
    commission_rate DOUBLE
);
```

### 契約階層構造の例

```
[メーカー契約] 
    ├─→ [代理店A契約] (ParentContract)
    │      ├─→ [代理店B契約] (ParentContract)
    │      │      └─→ [エンドユーザー契約] (ParentContract)
    │      └─→ [代理店C契約] (ParentContract)
    └─→ [代理店D契約] (ParentContract)
```

### ビジネスルール

1. **契約の継承**
   - 子契約は親契約の基本条件を継承
   - 子契約で上書き可能な条件を明示的に定義
   - 親契約が無効化された場合の子契約への影響を定義

2. **契約の有効性**
   - 親契約が有効でない場合、子契約は作成不可
   - 契約期間は親契約の期間内に収まる必要がある
   - 当事者の資格要件を満たす必要がある

3. **手数料・報酬の計算**
   - 多段階の手数料率は親契約から継承可能
   - 各レベルでの手数料上限を設定可能
   - 累積手数料の自動計算

### クエリ例

#### 特定企業の全契約階層を取得
```cypher
MATCH (p:Party {id: $party_id})-[:ContractParty]-(c:Contract)
MATCH path = (c)-[:ParentContract*0..]->(root:Contract)
WHERE NOT EXISTS { (root)-[:ParentContract]->(:Contract) }
RETURN path;
```

#### アクティブな紹介チェーンを取得
```cypher
MATCH chain = (referrer:Party)-[:ReferralChain*]->(referred:Party)
WHERE ALL(r IN relationships(chain) WHERE 
    EXISTS { 
        MATCH (c:Contract {id: r.contract_id})
        WHERE c.status = 'active'
    }
)
RETURN chain;
```

### セキュリティ考慮事項

1. **アクセス制御**
   - 契約階層に基づいたデータアクセス制限
   - 当事者は自身が関わる契約のみ閲覧可能
   - 親契約の当事者は子契約を閲覧可能（設定による）

2. **監査証跡**
   - 全ての契約変更履歴を記録
   - 契約条件の変更は新バージョンとして管理
   - 削除は論理削除のみ（物理削除不可）

3. **データ暗号化**
   - 機密条項（手数料率等）は暗号化して保存
   - 個人情報は別途暗号化
   - 通信時のTLS必須

## システムコンポーネント一覧

### データ層
- **Contract Entity** - 契約基本情報
- **Party Entity** - 契約当事者情報
- **GraphDB Schema** - 階層構造定義
- **Audit Log** - 監査証跡
- **Event Store** - イベント履歴

### ドメイン層
- **Contract Aggregate** - 契約集約
- **Party Aggregate** - 当事者集約
- **Contract Validator** - 契約検証ロジック
- **Hierarchy Manager** - 階層構造管理
- **Contract Lifecycle** - 契約ライフサイクル管理

### アプリケーション層
- **Contract Service** - 契約CRUD操作
- **Party Service** - 当事者管理
- **Search Service** - 契約検索
- **Notification Service** - 通知管理
- **Workflow Engine** - 承認フロー

### インフラ層
- **GraphDB Repository** - Kuzu接続
- **Event Publisher** - イベント発行
- **Cache Layer** - Redis等
- **File Storage** - 契約書保存
- **Email Gateway** - メール送信

### セキュリティ層
- **Authentication** - 認証
- **Authorization (RBAC)** - 認可
- **Encryption Service** - 暗号化
- **Token Manager** - トークン管理
- **Access Control** - アクセス制御

### 監視層
- **Metrics Collector** - メトリクス収集
- **Log Aggregator** - ログ集約
- **Trace Service** - 分散トレース
- **Alert Manager** - アラート管理
- **Health Check** - ヘルスチェック

### API層
- **REST API** - 外部API
- **GraphQL API** - クエリAPI
- **Webhook Manager** - Webhook管理
- **API Gateway** - APIゲートウェイ
- **Rate Limiter** - レート制限

### パターン別コンポーネント（選択式）
- **Commission Calculator** - 手数料計算
- **Discount Engine** - 割引計算
- **Referral Tracker** - 紹介追跡
- **Revenue Splitter** - 収益分配
- **Pattern-Specific Rules** - パターン別ルール

### レポート層（パターン別）
- **Sales Dashboard** - 販売ダッシュボード
- **Network Analytics** - ネットワーク分析
- **Commission Report** - 手数料レポート
- **Growth Metrics** - 成長指標
- **Export Service** - データエクスポート

### 統合層
- **External API Client** - 外部API連携
- **Import Service** - データインポート
- **Migration Tool** - データ移行
- **Sync Service** - 同期サービス
- **Integration Adapter** - 統合アダプター

## 実装優先順位

### Phase 1: MVP（必須機能）
1. Contract Entity
2. Party Entity
3. GraphDB Schema
4. Contract Service
5. Authentication/Authorization
6. REST API
7. 選択したパターンの基本ロジック

### Phase 2: 実用化
1. Audit Log
2. Notification Service
3. Workflow Engine
4. 選択したパターンの詳細機能
5. 基本的なダッシュボード

### Phase 3: 拡張
1. 他パターンへの対応
2. 高度な分析機能
3. 外部システム連携
4. パフォーマンス最適化