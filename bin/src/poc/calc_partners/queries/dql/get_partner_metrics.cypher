// Get Partner Metrics Query
// Purpose: Retrieve comprehensive metrics for partner performance analysis
// Parameters: partnerId, timeframe
// Returns: Complete partner metrics dashboard data

MATCH (p:Partner {id: $partnerId})
OPTIONAL MATCH (p)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[:ACQUIRED]->(customers:Customer)
WHERE customers.acquisitionDate >= $startDate AND customers.acquisitionDate <= $endDate
OPTIONAL MATCH (p)-[:INCURRED_COST]->(costs:Cost)
WHERE costs.timestamp >= $startDate AND costs.timestamp <= $endDate
OPTIONAL MATCH (p)-[:HAS_REWARD_STRUCTURE]->(rs:RewardStructure)
OPTIONAL MATCH (p)-[:HAS_TIER_STRUCTURE]->(ts:TierStructure)
WITH p, rs, ts,
     COUNT(DISTINCT t) AS totalTransactions,
     SUM(t.amount) AS totalRevenue,
     AVG(t.amount) AS avgTransactionValue,
     MAX(t.amount) AS maxTransactionValue,
     MIN(t.amount) AS minTransactionValue,
     COUNT(DISTINCT customers) AS customersAcquired,
     SUM(costs.amount) AS totalCosts,
     AVG(c.contributionScore) AS avgContributionScore
WITH p, rs, ts, totalTransactions, totalRevenue, avgTransactionValue,
     maxTransactionValue, minTransactionValue, customersAcquired, totalCosts, avgContributionScore,
     CASE 
       WHEN customersAcquired > 0 THEN totalCosts / customersAcquired
       ELSE 0
     END AS costPerAcquisition,
     CASE 
       WHEN totalCosts > 0 THEN ((totalRevenue - totalCosts) / totalCosts) * 100
       ELSE 0
     END AS roi
// Calculate tier status
WITH p, rs, ts, totalTransactions, totalRevenue, avgTransactionValue,
     maxTransactionValue, minTransactionValue, customersAcquired, totalCosts, 
     avgContributionScore, costPerAcquisition, roi,
     CASE
       WHEN totalRevenue >= COALESCE(ts.platinumThreshold, 100000) AND avgContributionScore >= 0.8 THEN 'PLATINUM'
       WHEN totalRevenue >= COALESCE(ts.goldThreshold, 50000) AND avgContributionScore >= 0.6 THEN 'GOLD'
       WHEN totalRevenue >= COALESCE(ts.silverThreshold, 20000) AND avgContributionScore >= 0.4 THEN 'SILVER'
       ELSE 'BRONZE'
     END AS currentTier
RETURN p.id AS partnerId,
       p.name AS partnerName,
       p.type AS partnerType,
       p.status AS partnerStatus,
       p.joinDate AS joinDate,
       currentTier AS currentTier,
       totalTransactions AS totalTransactions,
       totalRevenue AS totalRevenue,
       avgTransactionValue AS avgTransactionValue,
       maxTransactionValue AS maxTransactionValue,
       minTransactionValue AS minTransactionValue,
       customersAcquired AS customersAcquired,
       totalCosts AS totalCosts,
       costPerAcquisition AS costPerAcquisition,
       roi AS roiPercentage,
       avgContributionScore AS avgContributionScore,
       rs.type AS rewardStructureType,
       CASE 
         WHEN roi > 100 THEN 'EXCELLENT'
         WHEN roi > 50 THEN 'GOOD'
         WHEN roi > 0 THEN 'FAIR'
         ELSE 'POOR'
       END AS performanceRating