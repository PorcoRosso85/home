# DQL層 フラット構造（最終形）

## 構造原則：全クエリをdql/直下にフラット配置

```
dql/
├── flake.nix
├── package.json
├── test-helper.ts
│
├── uc01_partner_ltv_ranking.cypher              # 現状把握
├── uc01_partner_ltv_ranking.test.ts
├── uc02_partner_roi_analysis.cypher             # 現状把握
├── uc02_partner_roi_analysis.test.ts
├── uc03_reward_plan_simulation.cypher           # シミュレーション
├── uc03_reward_plan_simulation.test.ts
├── uc04_customer_profile_analysis.cypher        # 現状把握
├── uc04_customer_profile_analysis.test.ts
├── uc05_retention_rate_comparison.cypher        # 現状把握
├── uc05_retention_rate_comparison.test.ts
├── uc06_partner_relationship_discovery.cypher   # 現状把握
├── uc06_partner_relationship_discovery.test.ts
├── uc07_attribution_path_analysis.cypher        # 現状把握
├── uc07_attribution_path_analysis.test.ts
│
├── uc08_reward_model_generator.cypher           # 生成 ★新規
├── uc08_reward_model_generator.test.ts
├── uc09_dynamic_simulation.cypher               # シミュレーション ★新規
├── uc09_dynamic_simulation.test.ts
├── uc10_tiered_model_generator.cypher           # 生成 ★新規
├── uc10_tiered_model_generator.test.ts
├── uc11_cashflow_projection.cypher              # 予測 ★新規
├── uc11_cashflow_projection.test.ts
├── uc12_growth_projection.cypher                # 予測 ★新規
├── uc12_growth_projection.test.ts
├── uc13_optimal_rate_finder.cypher              # 最適化 ★新規
├── uc13_optimal_rate_finder.test.ts
├── uc14_partner_mix_optimizer.cypher            # 最適化 ★新規
├── uc14_partner_mix_optimizer.test.ts
│
└── _archive/                                     # 未使用クエリ
```

## ナンバリング規則

- `uc01`〜`uc07`: 既存（現状把握系）
- `uc08`〜`uc10`: 生成系 ★新規
- `uc11`〜`uc12`: 予測系 ★新規
- `uc13`〜`uc14`: 最適化系 ★新規

## Baby Steps実装計画

### Step 1: UC08 報酬モデル生成器【最優先】
```
1.1: 価値の明文化（WHY）
    - 経営者の「どんな報酬プランにすればいいか分からない」を解決
    - 20種類のモデルから最適な3つを自動選択

1.2: 仕様の定義（WHAT）【RED】
    - 入力: monthlyPrice, avgDuration, maxCPA
    - 出力: TOP3の報酬モデル（type, cost, margin, score）
    - test: 20種類生成→スコアリング→3つ返却を検証

1.3: 実現（HOW）【GREEN】
    - UNWIND で20モデル生成
    - スコア計算（利益率70% + 実装容易性30%）
    - ORDER BY score DESC LIMIT 3

1.4: 検証（CHECK）
    - nix develop -c node --test uc08_reward_model_generator.test.ts

1.5: 改善（REFACTOR）
    - モデルパラメータの外部化を検討
```

### Step 2: UC09 動的シミュレーション【必須】
```
2.1: 価値の明文化（WHY）
    - リアルタイムでパラメータ調整→即座に未来が見える
    - 「この条件だとどうなる？」に即答

2.2: 仕様の定義（WHAT）【RED】
    - 入力: upfrontBonus, revenueShareRate, monthlyVolume, avgLTV
    - 出力: 36ヶ月分の月次収支とcumulativeProfit
    - test: スライダー値変更→グラフデータ更新を検証

2.3: 実現（HOW）【GREEN】
    - UNWIND range(1, 36) で月次展開
    - SUM() OVER で累積計算
    - 各月のキャッシュフロー返却

2.4: 検証（CHECK）
    - nix develop -c node --test uc09_dynamic_simulation.test.ts
```

### Step 3: UC11 キャッシュフロー予測【重要】
```
3.1: 価値の明文化（WHY）
    - 36ヶ月先までの資金計画が立てられる
    - 投資判断の根拠となる数値提供

3.2: 仕様の定義（WHAT）【RED】
    - 入力: 現在のパートナー数、成長率、報酬プラン
    - 出力: 月次CF、累積CF、損益分岐点
    - test: 成長シナリオ別の予測値検証

3.3: 実現（HOW）【GREEN】
    - 既存データから成長トレンド抽出
    - 将来予測値の計算
    - 損益分岐点の特定
```

### Step 4: UC13 最適レート発見【発展】
```
4.1: 価値の明文化（WHY）
    - 利益最大化する報酬率を自動発見
    - 試行錯誤なしで最適解を提示

4.2: 仕様の定義（WHAT）【RED】
    - 入力: 制約条件（最低利益率、最大支払額）
    - 出力: 最適報酬率と期待利益
    - test: 様々な制約下での最適化検証
```

## 実装優先順位

1. **必須（Phase 1）**: UC08, UC09 → 即座に価値提供
2. **重要（Phase 2）**: UC11, UC13 → 差別化要素  
3. **発展（Phase 3）**: UC10, UC12, UC14 → 競争優位性

## なぜフラット構造か？

- **シンプル**: ディレクトリ階層による複雑化を排除
- **明確**: uc番号で責務が一目瞭然
- **保守性**: 全クエリが同一階層で管理しやすい
- **DQL純粋性**: クエリファイルのみに集中（UIやロジックは別層）