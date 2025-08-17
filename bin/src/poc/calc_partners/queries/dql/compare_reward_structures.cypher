// Compare Reward Structures Query
// Purpose: Compare different reward structures and their effectiveness
// Parameters: timeframe, rewardStructureIds (optional)
// Returns: Comparative analysis of reward structure performance

MATCH (rs:RewardStructure)
WHERE ($rewardStructureIds IS NULL OR rs.id IN $rewardStructureIds)
OPTIONAL MATCH (rs)<-[:HAS_REWARD_STRUCTURE]-(p:Partner)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
WITH rs,
     COUNT(DISTINCT p) AS partnersUsingStructure,
     COUNT(DISTINCT t) AS totalTransactions,
     SUM(t.amount) AS totalRevenue,
     AVG(t.amount) AS avgTransactionValue,
     AVG(c.contributionScore) AS avgContributionScore
WITH rs, partnersUsingStructure, totalTransactions, totalRevenue, avgTransactionValue, avgContributionScore,
     // Calculate reward costs based on structure type
     CASE rs.type
       WHEN 'percentage' THEN totalRevenue * rs.rate
       WHEN 'fixed' THEN totalTransactions * rs.fixedAmount
       WHEN 'tiered' THEN 
         SUM(
           CASE 
             WHEN t.amount >= rs.tier3Threshold THEN t.amount * rs.tier3Rate
             WHEN t.amount >= rs.tier2Threshold THEN t.amount * rs.tier2Rate
             ELSE t.amount * rs.tier1Rate
           END
         )
       ELSE 0
     END AS estimatedRewardCosts
WITH rs, partnersUsingStructure, totalTransactions, totalRevenue, avgTransactionValue, 
     avgContributionScore, estimatedRewardCosts,
     CASE 
       WHEN estimatedRewardCosts > 0 THEN (estimatedRewardCosts / totalRevenue) * 100
       ELSE 0
     END AS rewardCostPercentage,
     CASE 
       WHEN partnersUsingStructure > 0 THEN totalRevenue / partnersUsingStructure
       ELSE 0
     END AS revenuePerPartner
// Calculate efficiency metrics
WITH rs, partnersUsingStructure, totalTransactions, totalRevenue, avgTransactionValue,
     avgContributionScore, estimatedRewardCosts, rewardCostPercentage, revenuePerPartner,
     (totalRevenue - estimatedRewardCosts) AS netRevenue,
     CASE 
       WHEN estimatedRewardCosts > 0 THEN (totalRevenue - estimatedRewardCosts) / estimatedRewardCosts
       ELSE 0
     END AS returnOnRewardInvestment
// Get overall performance comparison
MATCH (allRS:RewardStructure)<-[:HAS_REWARD_STRUCTURE]-(allP:Partner)-[allC:CONTRIBUTED_TO]->(allT:Transaction)
WHERE allT.timestamp >= $startDate AND allT.timestamp <= $endDate
WITH rs, partnersUsingStructure, totalTransactions, totalRevenue, avgTransactionValue,
     avgContributionScore, estimatedRewardCosts, rewardCostPercentage, revenuePerPartner,
     netRevenue, returnOnRewardInvestment,
     AVG(allT.amount) AS overallAvgTransaction,
     AVG(allC.contributionScore) AS overallAvgContribution
RETURN rs.id AS rewardStructureId,
       rs.name AS structureName,
       rs.type AS structureType,
       partnersUsingStructure AS partnersCount,
       totalTransactions AS totalTransactions,
       totalRevenue AS totalRevenue,
       avgTransactionValue AS avgTransactionValue,
       avgContributionScore AS avgContributionScore,
       estimatedRewardCosts AS rewardCosts,
       rewardCostPercentage AS rewardCostPercent,
       netRevenue AS netRevenue,
       revenuePerPartner AS revenuePerPartner,
       returnOnRewardInvestment AS rewardROI,
       // Benchmarking
       CASE 
         WHEN avgTransactionValue > overallAvgTransaction THEN 'ABOVE_AVERAGE'
         WHEN avgTransactionValue >= overallAvgTransaction * 0.9 THEN 'AVERAGE'
         ELSE 'BELOW_AVERAGE'
       END AS transactionBenchmark,
       CASE 
         WHEN avgContributionScore > overallAvgContribution THEN 'ABOVE_AVERAGE'
         WHEN avgContributionScore >= overallAvgContribution * 0.9 THEN 'AVERAGE'
         ELSE 'BELOW_AVERAGE'
       END AS contributionBenchmark,
       // Efficiency rating
       CASE 
         WHEN returnOnRewardInvestment > 5 AND rewardCostPercentage < 10 THEN 'HIGHLY_EFFICIENT'
         WHEN returnOnRewardInvestment > 3 AND rewardCostPercentage < 15 THEN 'EFFICIENT'
         WHEN returnOnRewardInvestment > 1 THEN 'MODERATELY_EFFICIENT'
         ELSE 'INEFFICIENT'
       END AS efficiencyRating
ORDER BY returnOnRewardInvestment DESC