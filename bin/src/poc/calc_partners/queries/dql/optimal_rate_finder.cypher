// Optimal Rate Finder Query
// Finds the optimal reward rate that maximizes profit while maintaining partner satisfaction
// Parameters: $targetLtv, $minRate, $maxRate, $stepSize

WITH $targetLtv AS targetLtv,
     $minRate AS minRate,
     $maxRate AS maxRate,
     $stepSize AS stepSize

// Generate rate options
UNWIND range(0, ROUND((maxRate - minRate) / stepSize)) AS step
WITH targetLtv, minRate + step * stepSize AS rate

// Calculate metrics for each rate
WITH rate, targetLtv,
     targetLtv * rate AS cost,
     targetLtv - (targetLtv * rate) AS profit,
     // Partner satisfaction score (higher rate = higher satisfaction, but diminishing returns)
     100 * (1 - EXP(-3 * rate)) AS satisfactionScore,
     // Profitability score
     (targetLtv - targetLtv * rate) / targetLtv * 100 AS profitMargin

// Calculate combined optimization score
WITH rate, cost, profit, satisfactionScore, profitMargin,
     // Weighted score: 60% profit, 40% satisfaction
     profitMargin * 0.6 + satisfactionScore * 0.4 AS optimizationScore

// Find the optimal rate
ORDER BY optimizationScore DESC
LIMIT 5

RETURN 
  ROUND(rate * 100) AS ratePercent,
  ROUND(cost) AS totalCost,
  ROUND(profit) AS totalProfit,
  ROUND(profitMargin) AS profitMarginPercent,
  ROUND(satisfactionScore) AS partnerSatisfaction,
  ROUND(optimizationScore) AS score,
  CASE 
    WHEN rate < 0.10 THEN 'Low - Risk of partner churn'
    WHEN rate < 0.20 THEN 'Moderate - Balanced approach'
    WHEN rate < 0.30 THEN 'Good - Strong partner incentive'
    ELSE 'High - Premium partner program'
  END AS recommendation