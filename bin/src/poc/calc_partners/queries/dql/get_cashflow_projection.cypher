// Get Cashflow Projection Query
// Purpose: Project future cashflow based on partner relationships and historical data
// Parameters: projectionMonths, scenarioType (conservative/optimistic/realistic)
// Returns: Monthly cashflow projections with multiple scenarios

MATCH (p:Partner)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= date.sub($currentDate, duration({months: 12}))
WITH p,
     COUNT(t) AS historicalTransactions,
     SUM(t.amount) AS historicalRevenue,
     AVG(t.amount) AS avgTransactionValue,
     AVG(c.contributionScore) AS avgContribution
WITH p, historicalTransactions, historicalRevenue, avgTransactionValue, avgContribution,
     historicalRevenue / 12.0 AS monthlyRevenueBase,
     historicalTransactions / 12.0 AS monthlyTransactionBase
// Calculate growth rates from recent trends
MATCH (p)-[recentC:CONTRIBUTED_TO]->(recentT:Transaction)
WHERE recentT.timestamp >= date.sub($currentDate, duration({months: 3}))
WITH p, historicalTransactions, historicalRevenue, avgTransactionValue, avgContribution,
     monthlyRevenueBase, monthlyTransactionBase,
     COUNT(recentT) AS recentTransactions,
     SUM(recentT.amount) AS recentRevenue
WITH p, monthlyRevenueBase, monthlyTransactionBase, avgTransactionValue, avgContribution,
     (recentRevenue / 3.0) AS recentMonthlyRevenue,
     CASE 
       WHEN monthlyRevenueBase > 0 THEN ((recentRevenue / 3.0) - monthlyRevenueBase) / monthlyRevenueBase
       ELSE 0
     END AS growthTrend
// Get partner costs and reward structures
OPTIONAL MATCH (p)-[:INCURRED_COST]->(cost:Cost)
WHERE cost.timestamp >= date.sub($currentDate, duration({months: 12}))
OPTIONAL MATCH (p)-[:HAS_REWARD_STRUCTURE]->(rs:RewardStructure)
WITH p, monthlyRevenueBase, monthlyTransactionBase, avgTransactionValue, avgContribution,
     growthTrend, rs,
     COALESCE(SUM(cost.amount) / 12.0, 0) AS monthlyCostBase
WITH p, monthlyRevenueBase, monthlyTransactionBase, avgTransactionValue, avgContribution,
     growthTrend, rs, monthlyCostBase,
     // Scenario multipliers
     CASE COALESCE($scenarioType, 'realistic')
       WHEN 'conservative' THEN 0.8
       WHEN 'optimistic' THEN 1.3
       ELSE 1.0
     END AS scenarioMultiplier
// Generate projections for each month
UNWIND range(1, COALESCE($projectionMonths, 12)) AS monthOffset
WITH p, monthlyRevenueBase, monthlyCostBase, avgTransactionValue, growthTrend,
     rs, scenarioMultiplier, monthOffset,
     date.add($currentDate, duration({months: monthOffset})) AS projectionMonth
WITH p, monthlyRevenueBase, monthlyCostBase, avgTransactionValue, growthTrend,
     rs, scenarioMultiplier, monthOffset, projectionMonth,
     // Apply growth trend and scenario
     monthlyRevenueBase * (1 + (growthTrend * monthOffset * 0.1)) * scenarioMultiplier AS projectedRevenue
WITH p, monthlyCostBase, rs, monthOffset, projectionMonth, projectedRevenue,
     // Calculate projected costs with inflation
     monthlyCostBase * (1 + (monthOffset * 0.02)) AS projectedCosts,
     // Calculate reward costs
     CASE rs.type
       WHEN 'percentage' THEN projectedRevenue * rs.rate
       WHEN 'fixed' THEN (projectedRevenue / avgTransactionValue) * rs.fixedAmount
       ELSE projectedRevenue * 0.05  // Default 5% if no structure
     END AS projectedRewards
WITH p, monthOffset, projectionMonth, projectedRevenue, projectedCosts, projectedRewards,
     projectedRevenue - projectedCosts - projectedRewards AS netCashflow
// Aggregate by month across all partners
WITH projectionMonth, monthOffset,
     SUM(projectedRevenue) AS totalProjectedRevenue,
     SUM(projectedCosts) AS totalProjectedCosts,
     SUM(projectedRewards) AS totalProjectedRewards,
     SUM(netCashflow) AS totalNetCashflow
WITH projectionMonth, monthOffset, totalProjectedRevenue, totalProjectedCosts,
     totalProjectedRewards, totalNetCashflow,
     // Calculate cumulative cashflow
     SUM(totalNetCashflow) OVER (ORDER BY monthOffset) AS cumulativeCashflow
RETURN projectionMonth AS month,
       monthOffset AS monthsFromNow,
       totalProjectedRevenue AS projectedRevenue,
       totalProjectedCosts AS projectedCosts,
       totalProjectedRewards AS projectedRewards,
       totalNetCashflow AS netCashflow,
       cumulativeCashflow AS cumulativeCashflow,
       COALESCE($scenarioType, 'realistic') AS scenario,
       CASE 
         WHEN totalNetCashflow > 0 THEN 'POSITIVE'
         WHEN totalNetCashflow < 0 THEN 'NEGATIVE'
         ELSE 'BREAK_EVEN'
       END AS cashflowStatus
ORDER BY monthOffset