# パートナー報酬プラットフォーム実装計画

## 現状分析

### 既存UC（ユースケース）の評価
現在のUC1-UC7は**基盤として十分**です：

✅ **利用可能な基盤機能**
- UC1: Partner LTV Ranking → ランキング表示
- UC2: Partner ROI Analysis → 利益率計算ロジック ⭐️
- UC3: Reward Plan Simulation → シナリオ比較機能 ⭐️
- UC4: Customer Profile Analysis → 顧客セグメント分析
- UC5: Retention Rate Comparison → 品質指標
- UC6: Partner Relationship Discovery → ネットワーク分析
- UC7: Attribution Path Analysis → 貢献度追跡

## 実装可能性の回答

### 1. モデル作成 → **✅ 提供可能**

**報酬モデル・ジェネレーター**として実装可能：

```typescript
// generator.ts
interface RewardModelGenerator {
  // 入力パラメータ
  input: {
    businessModel: 'subscription' | 'onetime' | 'usage'
    avgMonthlyPrice: number
    avgContractMonths: number  
    maxCPA: number
    partnerExpectation: 'introduction' | 'closing' | 'support'
  }
  
  // 3つの報酬プラン自動生成
  generatePlans(): {
    conservative: RewardPlan   // 手堅い
    balanced: RewardPlan       // バランス型
    aggressive: RewardPlan     // 攻撃的
  }
}
```

**必要な新クエリ（UC8として追加）**：
```cypher
// uc8_generate_reward_models.cypher
// 入力パラメータから3つの報酬モデルを生成
WITH $ltv AS ltv, $maxCPA AS maxCPA
RETURN 
  // プランA: レベニューシェア型
  {
    name: 'Revenue Share',
    rate: maxCPA / ltv * 0.3,  // 保守的な30%
    type: 'percentage',
    duration: 12,
    totalCost: ltv * (maxCPA / ltv * 0.3),
    profitMargin: 1 - (maxCPA / ltv * 0.3)
  } AS conservative,
  
  // プランB: ハイブリッド型
  {
    name: 'Hybrid',
    upfront: maxCPA * 0.2,
    rate: maxCPA / ltv * 0.15,
    type: 'hybrid',
    duration: 24,
    totalCost: (maxCPA * 0.2) + (ltv * (maxCPA / ltv * 0.15)),
    profitMargin: 1 - ((maxCPA * 0.2 + ltv * (maxCPA / ltv * 0.15)) / ltv)
  } AS balanced,
  
  // プランC: ティア型
  {
    name: 'Tiered',
    tiers: [
      {min: 1, max: 5, rate: maxCPA / ltv * 0.25},
      {min: 6, max: 10, rate: maxCPA / ltv * 0.35},
      {min: 11, max: null, rate: maxCPA / ltv * 0.45}
    ],
    type: 'tiered',
    avgCost: maxCPA * 0.8,
    profitMargin: 0.2
  } AS aggressive
```

### 2. シミュレーター → **✅ 提供可能**

**リアルタイムシミュレーター**として実装可能：

```typescript
// simulator.ts
interface RealtimeSimulator {
  // スライダーで調整可能なパラメータ
  adjustableParams: {
    upfrontBonus: number       // 0 ~ 100,000円
    revenueShareRate: number   // 0 ~ 50%
    duration: number           // 1 ~ 36ヶ月
    expectedVolume: number     // 月間獲得数
  }
  
  // リアルタイム再計算
  simulate(): {
    cashflow: MonthlyProjection[]  // 36ヶ月分
    totalCost: number
    profitMargin: number
    breakEvenMonth: number
    roi: number
  }
}
```

**UC3の拡張版（UC9として追加）**：
```cypher
// uc9_realtime_simulation.cypher
// パラメータをリアルタイムで調整してシミュレーション
WITH 
  $upfrontBonus AS upfront,
  $revenueShare AS share,
  $monthlyVolume AS volume,
  $avgLTV AS ltv
UNWIND range(1, 36) AS month
RETURN 
  month,
  volume * upfront AS monthlyUpfront,  // 初期コスト
  volume * ltv * share / 12 AS monthlyRevShare,  // 月次支払
  volume * ltv / 12 AS monthlyRevenue,  // 月次収益
  (volume * ltv / 12) - (volume * upfront + volume * ltv * share / 12) AS monthlyProfit,
  SUM((volume * ltv / 12) - (volume * upfront + volume * ltv * share / 12)) OVER (ORDER BY month) AS cumulativeProfit
```

## 実装アーキテクチャ

```
┌─────────────────────────────────────┐
│         フロントエンド (Next.js)      │
│  ・入力フォーム                       │
│  ・リアルタイムスライダー               │
│  ・グラフ表示 (Chart.js)              │
└──────────────┬──────────────────────┘
               │ REST API / GraphQL
┌──────────────▼──────────────────────┐
│     ビジネスロジック層 (Node.js)      │
│  ・RewardModelGenerator              │
│  ・RealtimeSimulator                 │
│  ・CashflowProjector                 │
└──────────────┬──────────────────────┘
               │ Cypher Queries
┌──────────────▼──────────────────────┐
│      データ層 (KuzuDB WASM)          │
│  ・UC1-UC7: 分析基盤 ✅               │
│  ・UC8: モデル生成 (新規)             │
│  ・UC9: リアルタイムシミュレーション (新規) │
└─────────────────────────────────────┘
```

## 実装ステップ

### Phase 1: 基盤強化（1週間）
1. UC8（報酬モデル生成）クエリ作成
2. UC9（リアルタイムシミュレーション）クエリ作成
3. テストケース追加

### Phase 2: APIレイヤー（1週間）
1. RewardModelGenerator実装
2. RealtimeSimulator実装
3. REST API / GraphQLエンドポイント

### Phase 3: UI実装（2週間）
1. 入力フォームコンポーネント
2. スライダーコンポーネント
3. グラフ表示（Chart.js統合）
4. レスポンシブデザイン

### Phase 4: 統合テスト（1週間）
1. E2Eテスト
2. パフォーマンステスト
3. ユーザビリティテスト

## 結論

**全て提供可能です。**

現在のUC1-UC7は十分な基盤となっており、UC8（モデル生成）とUC9（リアルタイムシミュレーション）を追加することで、ビジョンの「報酬モデル・ジェネレーター」と「リアルタイムシミュレーター」を完全に実現できます。

KuzuDB WASMを使った高速なグラフクエリにより、パラメータ変更時の即座な再計算が可能で、まさに「経営者の外部ブレイン」として機能します。