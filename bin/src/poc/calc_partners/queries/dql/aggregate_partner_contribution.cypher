// Aggregate Partner Contribution Query
// Purpose: Aggregate and analyze partner contributions across different dimensions
// Parameters: timeframe, contributionType (revenue/transactions/customers)
// Returns: Partner contribution analysis with rankings and comparisons

MATCH (p:Partner)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[:ACQUIRED]->(customers:Customer)
WHERE customers.acquisitionDate >= $startDate AND customers.acquisitionDate <= $endDate
OPTIONAL MATCH (p)-[:INCURRED_COST]->(costs:Cost)
WHERE costs.timestamp >= $startDate AND costs.timestamp <= $endDate
OPTIONAL MATCH (p)-[:HAS_REWARD_STRUCTURE]->(rs:RewardStructure)
WITH p, rs,
     COUNT(DISTINCT t) AS totalTransactions,
     SUM(t.amount) AS totalRevenue,
     COUNT(DISTINCT customers) AS customersAcquired,
     SUM(costs.amount) AS totalCosts,
     AVG(c.contributionScore) AS avgContributionScore,
     SUM(t.amount * c.contributionScore) AS weightedRevenue
// Calculate reward costs
WITH p, rs, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue,
     CASE rs.type
       WHEN 'percentage' THEN totalRevenue * rs.rate
       WHEN 'fixed' THEN totalTransactions * rs.fixedAmount
       WHEN 'tiered' THEN 
         // Simplified tiered calculation - would need more complex logic for actual implementation
         totalRevenue * COALESCE(rs.tier1Rate, 0.05)
       ELSE totalRevenue * 0.05
     END AS rewardCosts
WITH p, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue, rewardCosts,
     totalRevenue - totalCosts - rewardCosts AS netContribution
// Get overall totals for percentage calculations
MATCH (allP:Partner)-[allC:CONTRIBUTED_TO]->(allT:Transaction)
WHERE allT.timestamp >= $startDate AND allT.timestamp <= $endDate
WITH p, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue, rewardCosts, netContribution,
     SUM(allT.amount) AS totalMarketRevenue,
     COUNT(DISTINCT allT) AS totalMarketTransactions,
     SUM(allT.amount * allC.contributionScore) AS totalWeightedRevenue
WITH p, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue, rewardCosts, netContribution,
     totalMarketRevenue, totalMarketTransactions, totalWeightedRevenue,
     // Calculate contribution percentages
     CASE 
       WHEN totalMarketRevenue > 0 THEN (totalRevenue / totalMarketRevenue) * 100
       ELSE 0
     END AS revenueContributionPercent,
     CASE 
       WHEN totalMarketTransactions > 0 THEN (totalTransactions / toFloat(totalMarketTransactions)) * 100
       ELSE 0
     END AS transactionContributionPercent,
     CASE 
       WHEN totalWeightedRevenue > 0 THEN (weightedRevenue / totalWeightedRevenue) * 100
       ELSE 0
     END AS weightedContributionPercent
// Calculate efficiency metrics
WITH p, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue, rewardCosts, netContribution,
     revenueContributionPercent, transactionContributionPercent, weightedContributionPercent,
     CASE 
       WHEN totalCosts > 0 THEN (netContribution / totalCosts) * 100
       ELSE 0
     END AS efficiencyRatio,
     CASE 
       WHEN customersAcquired > 0 THEN totalRevenue / customersAcquired
       ELSE 0
     END AS revenuePerCustomer,
     CASE 
       WHEN totalTransactions > 0 THEN totalRevenue / totalTransactions
       ELSE 0
     END AS revenuePerTransaction
// Add rankings
WITH p, totalTransactions, totalRevenue, customersAcquired, totalCosts,
     avgContributionScore, weightedRevenue, rewardCosts, netContribution,
     revenueContributionPercent, transactionContributionPercent, weightedContributionPercent,
     efficiencyRatio, revenuePerCustomer, revenuePerTransaction,
     ROW_NUMBER() OVER (ORDER BY totalRevenue DESC) AS revenueRank,
     ROW_NUMBER() OVER (ORDER BY weightedRevenue DESC) AS weightedRevenueRank,
     ROW_NUMBER() OVER (ORDER BY netContribution DESC) AS netContributionRank,
     ROW_NUMBER() OVER (ORDER BY efficiencyRatio DESC) AS efficiencyRank
RETURN p.id AS partnerId,
       p.name AS partnerName,
       p.type AS partnerType,
       p.status AS partnerStatus,
       // Core metrics
       totalTransactions AS transactionCount,
       totalRevenue AS revenue,
       weightedRevenue AS weightedRevenue,
       customersAcquired AS customersAcquired,
       avgContributionScore AS avgContributionScore,
       // Financial metrics
       totalCosts AS costs,
       rewardCosts AS rewardCosts,
       netContribution AS netContribution,
       // Contribution percentages
       revenueContributionPercent AS revenueContributionPercent,
       transactionContributionPercent AS transactionContributionPercent,
       weightedContributionPercent AS weightedContributionPercent,
       // Efficiency metrics
       efficiencyRatio AS efficiencyRatio,
       revenuePerCustomer AS revenuePerCustomer,
       revenuePerTransaction AS revenuePerTransaction,
       // Rankings
       revenueRank AS revenueRank,
       weightedRevenueRank AS weightedRevenueRank,
       netContributionRank AS netContributionRank,
       efficiencyRank AS efficiencyRank,
       // Performance categorization
       CASE 
         WHEN revenueContributionPercent > 20 THEN 'TOP_CONTRIBUTOR'
         WHEN revenueContributionPercent > 10 THEN 'MAJOR_CONTRIBUTOR'
         WHEN revenueContributionPercent > 5 THEN 'SIGNIFICANT_CONTRIBUTOR'
         WHEN revenueContributionPercent > 1 THEN 'MINOR_CONTRIBUTOR'
         ELSE 'MINIMAL_CONTRIBUTOR'
       END AS contributionTier
ORDER BY 
  CASE COALESCE($contributionType, 'revenue')
    WHEN 'weighted' THEN weightedRevenue
    WHEN 'transactions' THEN totalTransactions
    WHEN 'customers' THEN customersAcquired
    WHEN 'efficiency' THEN efficiencyRatio
    ELSE totalRevenue
  END DESC