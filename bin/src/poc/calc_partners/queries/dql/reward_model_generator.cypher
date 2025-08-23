// Reward Model Generator Query
// Generates 20 reward models and returns TOP3 by score
// Parameters: $monthlyPrice, $avgContractMonths, $maxCPA

WITH $monthlyPrice AS monthlyPrice,
     $avgContractMonths AS avgContractMonths,
     $maxCPA AS maxCPA,
     monthlyPrice * avgContractMonths AS ltv

// Generate 20 models using UNWIND
UNWIND range(1, 20) AS modelId
WITH modelId, ltv, maxCPA,
     // Vary the rate from 5% to 45%
     0.05 + (modelId - 1) * 0.02 AS rate,
     CASE 
       WHEN modelId <= 7 THEN 'conservative'
       WHEN modelId <= 14 THEN 'balanced'
       ELSE 'aggressive'
     END AS planType

// Calculate metrics for each model
WITH modelId, planType, rate, ltv, maxCPA,
     ltv * rate AS totalCost,
     ltv - (ltv * rate) AS profit

// Calculate score (profit margin + type bonus)
WITH modelId, planType, rate, totalCost, profit,
     (profit / ltv) * 100 AS profitMargin,
     (profit / ltv) * 100 + 
     CASE planType 
       WHEN 'conservative' THEN 10
       WHEN 'balanced' THEN 5
       ELSE 0
     END AS score

// Return TOP3 by score
ORDER BY score DESC
LIMIT 3

RETURN 
  planType,
  rate * 100 AS ratePercent,
  profitMargin,
  score,
  totalCost AS rewardAmount,
  profit