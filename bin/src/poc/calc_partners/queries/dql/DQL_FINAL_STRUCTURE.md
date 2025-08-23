# DQL層の責務と最終構造

## DQL（Data Query Layer）の責務定義
**DQLは「問い」に答える層**です。データの読み取り専用で、ビジネス上の質問に対する答えを返します。

## 最終ディレクトリ構造

```
dql/
├── flake.nix                              # Nix環境定義
├── package.json                           # Node.js依存関係
├── test-helper.ts                         # テストユーティリティ
│
├── core/                                  # 【基礎分析クエリ】
│   ├── uc1_partner_ltv_ranking.cypher            # パートナー別LTV順位
│   ├── uc1_partner_ltv_ranking.test.ts           
│   ├── uc2_partner_roi_analysis.cypher           # ROI分析
│   ├── uc2_partner_roi_analysis.test.ts          
│   ├── uc4_customer_profile_analysis.cypher      # 顧客プロファイル
│   ├── uc4_customer_profile_analysis.test.ts     
│   ├── uc5_retention_rate_comparison.cypher      # リテンション比較
│   ├── uc5_retention_rate_comparison.test.ts     
│   ├── uc6_partner_relationship_discovery.cypher # 関係性発見
│   ├── uc6_partner_relationship_discovery.test.ts
│   ├── uc7_attribution_path_analysis.cypher      # アトリビューション
│   └── uc7_attribution_path_analysis.test.ts     
│
├── simulation/                            # 【シミュレーション系クエリ】
│   ├── uc3_reward_plan_simulation.cypher         # 静的シナリオ比較
│   ├── uc3_reward_plan_simulation.test.ts        
│   ├── uc9_dynamic_simulation.cypher             # 動的パラメータ調整 ★新規
│   └── uc9_dynamic_simulation.test.ts            
│
├── generator/                             # 【生成系クエリ】
│   ├── uc8_reward_model_generator.cypher         # 報酬モデル生成 ★新規
│   ├── uc8_reward_model_generator.test.ts        
│   ├── uc10_tiered_model_generator.cypher        # 階層型モデル生成 ★新規
│   └── uc10_tiered_model_generator.test.ts       
│
├── projection/                            # 【予測系クエリ】  
│   ├── uc11_cashflow_projection.cypher           # CF予測 ★新規
│   ├── uc11_cashflow_projection.test.ts          
│   ├── uc12_growth_projection.cypher             # 成長予測 ★新規
│   └── uc12_growth_projection.test.ts            
│
├── optimization/                          # 【最適化系クエリ】
│   ├── uc13_optimal_rate_finder.cypher           # 最適レート発見 ★新規
│   ├── uc13_optimal_rate_finder.test.ts          
│   ├── uc14_partner_mix_optimizer.cypher         # パートナーMix最適化 ★新規
│   └── uc14_partner_mix_optimizer.test.ts        
│
└── _archive/                              # アーカイブ（現状維持）
    └── [既存の20個のクエリファイル]
```

## 責務マッピング

### 1. core/ - 基礎分析（現状把握）
**責務**: 「今どうなっているか？」に答える
- UC1: 「どのパートナーが最も価値が高いか？」
- UC2: 「各パートナーのROIは？」
- UC4: 「パートナー別の顧客特性は？」
- UC5: 「獲得チャネル別の品質は？」
- UC6: 「パートナー間の関係性は？」
- UC7: 「顧客獲得の経路は？」

### 2. simulation/ - What-If分析
**責務**: 「もし〜したらどうなるか？」に答える
- UC3: 「報酬率を変更したら支払額は？」
- UC9: 「パラメータをリアルタイムで調整したら？」★新規

### 3. generator/ - モデル生成
**責務**: 「どんな選択肢があるか？」を提示する
- UC8: 「LTVとCPAから最適な報酬モデルは？」★新規
- UC10: 「階層型報酬の最適な段階設定は？」★新規

### 4. projection/ - 将来予測
**責務**: 「このままいくとどうなるか？」を予測する
- UC11: 「今後36ヶ月のキャッシュフローは？」★新規
- UC12: 「成長率を考慮した将来収益は？」★新規

### 5. optimization/ - 最適化提案
**責務**: 「最も良い選択は何か？」を提案する
- UC13: 「利益最大化する報酬率は？」★新規
- UC14: 「最適なパートナーポートフォリオは？」★新規

## DQL層が守るべき原則

1. **読み取り専用**: DQLはデータを変更しない（SELECTのみ）
2. **質問への回答**: 各クエリは明確なビジネス上の質問に答える
3. **再利用可能**: パラメータ化により様々な条件で実行可能
4. **テスト可能**: 各クエリにテストケースを必須とする
5. **独立性**: 各クエリは他のクエリに依存しない

## 実装優先順位

### Phase 1: 即座に価値を提供（必須）
- ✅ UC1-UC7: 完了済み
- 🔨 UC8: 報酬モデル生成
- 🔨 UC9: 動的シミュレーション

### Phase 2: 差別化要素（重要）
- UC11: キャッシュフロー予測
- UC13: 最適レート発見

### Phase 3: 競争優位性（発展）
- UC10: 階層型モデル生成
- UC12: 成長予測
- UC14: パートナーMix最適化

## なぜこの構造か？

この構造により、DQL層は純粋に「問いに答える」責務に集中できます。
- **ビジネスロジック層**が「どの問いを投げるか」を決定
- **DQL層**が「その問いに対する答え」を返す
- **UI層**が「答えをどう見せるか」を制御

これが**責務の分離**であり、各層が単一の責任を持つことで、保守性と拡張性を確保します。