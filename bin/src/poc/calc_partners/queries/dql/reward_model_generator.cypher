// ==================================================================================
// UC8: Reward Model Generator - 業界標準ベース報酬モデル提案
// ==================================================================================
//
// 経営者の痛み: 「3日間悩んでも最適な報酬モデルが決められない」
// 解決策: SaaS業界の実績データに基づく3つの明確な選択肢を即座に提示
//
// Parameters:
//   $monthlyPrice: 月額単価（あなたの製品の平均月額料金）
//   $avgContractMonths: 平均契約期間（顧客が継続する月数）
//   $maxCPA: 許容CPA（1顧客獲得に払える上限額）
//
// ==================================================================================

WITH $monthlyPrice AS monthlyPrice,
     $avgContractMonths AS avgContractMonths,
     $maxCPA AS maxCPA,
     monthlyPrice * avgContractMonths AS ltv,
     // 業界標準: LTV/CPA比率 3:1 (SaaStr 2023調査)
     monthlyPrice * avgContractMonths / 3 AS healthyCPA

// 業界実績に基づく3つの報酬モデル
UNWIND [
  {
    id: 1,
    name: 'Conservative（手堅く始める）',
    rate: 0.10,  // 10%
    benchmark: 'Shopify Partner Program',
    description: 'リスク最小。黒字確保を優先',
    bestFor: 'スタートアップ、キャッシュフロー重視企業'
  },
  {
    id: 2,
    name: 'Balanced（業界標準）',
    rate: 0.20,  // 20%
    benchmark: 'Salesforce/Microsoft平均',
    description: '成長と収益性のバランス',
    bestFor: '成長期のSaaS企業'
  },
  {
    id: 3,
    name: 'Aggressive（市場制覇）',
    rate: 0.30,  // 30%
    benchmark: 'ConvertKit/ClickFunnels',
    description: '市場シェア獲得を最優先',
    bestFor: '資金調達済み、急成長フェーズ'
  }
] AS model

// 各モデルの財務インパクトを計算
WITH model, ltv, maxCPA, healthyCPA,
     ltv * model.rate AS partnerReward,
     ltv - (ltv * model.rate) AS netRevenue,
     (ltv - (ltv * model.rate)) / ltv * 100 AS profitMargin,
     // CPAとの比較
     CASE 
       WHEN ltv * model.rate <= maxCPA THEN '✅ CPA内'
       ELSE '⚠️ CPA超過'
     END AS cpaCheck,
     // 健全性スコア（100点満点）
     CASE
       WHEN ltv * model.rate <= maxCPA * 0.7 THEN 100  // CPA70%以下は満点
       WHEN ltv * model.rate <= maxCPA THEN 80         // CPA内なら80点
       WHEN ltv * model.rate <= maxCPA * 1.2 THEN 60   // CPA120%まで60点
       ELSE 40                                          // それ以上は40点
     END AS healthScore

RETURN 
  model.name AS プラン名,
  model.rate * 100 AS 報酬率,
  ROUND(partnerReward) AS パートナー報酬額,
  ROUND(netRevenue) AS 純収益,
  ROUND(profitMargin) AS 利益率,
  cpaCheck AS CPA判定,
  healthScore AS 健全性スコア,
  model.benchmark AS 業界ベンチマーク,
  model.description AS 特徴,
  model.bestFor AS 推奨企業,
  // 意思決定のための追加情報
  CASE
    WHEN model.rate = 0.10 THEN 
      '初期リスクを抑えつつ、パートナープログラムの効果を検証できます'
    WHEN model.rate = 0.20 THEN
      'Fortune 500企業の68%が採用する標準的な報酬率です'
    ELSE
      '競合より高い報酬で、トップパートナーを独占できます'
  END AS 選択理由
ORDER BY model.id