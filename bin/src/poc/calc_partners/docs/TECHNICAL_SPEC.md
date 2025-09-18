# 技術仕様書 - SaaS Partner Calculator

## アーキテクチャ概要

### 設計原則
- **単一責務**: 計算とシミュレーションのみ
- **ステートレス**: 計算ロジックは純粋関数
- **イミュータブル**: データ変更は新規作成
- **型安全**: 全ての計算パラメータを型定義

## コア機能仕様

### 1. 報酬モデル・ジェネレーター

#### データ型定義
```typescript
interface BusinessModel {
  type: 'subscription' | 'usage_based' | 'hybrid';
  monthlyFee?: number;
  usageRate?: number;
  setupFee?: number;
}

interface CustomerMetrics {
  averageLTV: number;
  averageUnitPrice: number;
  allowableCPA: number;
  churnRate: number;
}

interface PartnerType {
  type: 'referral' | 'reseller' | 'influencer';
  characteristics: {
    volumeCapacity: 'low' | 'medium' | 'high';
    supportLevel: 'none' | 'basic' | 'full';
  };
}

interface RewardModel {
  modelName: string;
  structure: 'revenue_share' | 'fixed_plus_incentive' | 'tiered';
  parameters: {
    baseRate: number;
    incentiveRate?: number;
    tiers?: TierDefinition[];
  };
  projectedROI: number;
  breakEvenPoint: number;
}
```

#### 計算ロジック
```typescript
function generateRewardModels(
  business: BusinessModel,
  metrics: CustomerMetrics,
  partner: PartnerType
): RewardModel[] {
  // 勝ちパターンの計算ロジック
  // 1. パートナータイプ別の最適レート算出
  // 2. ROI最大化の観点から複数モデル生成
  // 3. リスク・リターンのバランス評価
}
```

### 2. リアルタイム収益シミュレーター

#### シミュレーションパラメータ
```typescript
interface SimulationParams {
  timeHorizon: number; // months
  variables: {
    partnerGrowthRate: number;
    customerAcquisitionRate: number;
    churnRate: number;
    priceChangeRate: number;
  };
  rewardModel: RewardModel;
}

interface SimulationResult {
  timeline: TimePoint[];
  metrics: {
    totalRevenue: number;
    partnerPayout: number;
    netProfit: number;
    roi: number;
  };
}

interface TimePoint {
  month: number;
  revenue: number;
  partnerCount: number;
  customerCount: number;
  cashFlow: number;
}
```

#### 計算エンジン
```typescript
class SimulationEngine {
  private calculateMonthlyMetrics(
    previousState: TimePoint,
    params: SimulationParams
  ): TimePoint {
    // モンテカルロシミュレーション
    // 確率的変動を考慮した予測
  }
  
  public runSimulation(params: SimulationParams): SimulationResult {
    // 時系列でのキャッシュフロー計算
    // 複利効果の反映
  }
}
```

### 3. API連携仕様

#### Stripe連携
```typescript
interface StripeIntegration {
  async fetchRevenueData(
    startDate: Date,
    endDate: Date
  ): Promise<RevenueData>;
  
  async fetchCustomerMetrics(): Promise<CustomerMetrics>;
}
```

#### Salesforce/HubSpot連携
```typescript
interface CRMIntegration {
  async fetchPartnerData(): Promise<PartnerData[]>;
  async fetchCustomerSegmentation(): Promise<SegmentData[]>;
}
```

## データフロー

```
[External APIs] → [Data Adapter] → [Calculation Engine] → [Results]
     ↑                                      ↓
[User Input] ────────────────────→ [Simulation Engine]
                                           ↓
                                    [Visualization]
```

## パフォーマンス要件

### レスポンスタイム
- 報酬モデル生成: < 100ms
- シミュレーション実行: < 500ms
- グラフ更新: < 50ms

### スケーラビリティ
- 同時接続: 1000ユーザー
- データポイント: 100万レコード/ユーザー
- API呼び出し: 10,000回/日

## セキュリティ要件

### データ保護
- API認証: OAuth 2.0
- 通信: TLS 1.3
- データ暗号化: AES-256

### アクセス制御
- ロールベース権限管理
- APIレート制限
- 監査ログ

## エラーハンドリング

### 計算エラー
```typescript
class CalculationError extends Error {
  constructor(
    public code: string,
    public context: any,
    message: string
  ) {
    super(message);
  }
}
```

### API連携エラー
- リトライ機構（指数バックオフ）
- フォールバック（キャッシュデータ使用）
- エラー通知（ログ記録）

## テスト戦略

### 単体テスト
- 計算ロジックの正確性
- エッジケースの処理
- 型安全性の保証

### 統合テスト
- API連携の動作確認
- エンドツーエンドフロー
- パフォーマンステスト

### プロパティベーステスト
- 計算結果の不変条件
- シミュレーションの収束性
- データ整合性