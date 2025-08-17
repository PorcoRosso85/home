// Analyze Partner Performance Query
// Purpose: Deep analysis of partner performance trends and comparative metrics
// Parameters: partnerId (optional), timeframe, comparisonPeriod
// Returns: Performance analysis with trends and comparisons

MATCH (p:Partner)
WHERE ($partnerId IS NULL OR p.id = $partnerId)
OPTIONAL MATCH (p)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[prevC:CONTRIBUTED_TO]->(prevT:Transaction)
WHERE prevT.timestamp >= $comparisonStartDate AND prevT.timestamp <= $comparisonEndDate
WITH p,
     // Current period metrics
     COUNT(DISTINCT t) AS currentTransactions,
     SUM(t.amount) AS currentRevenue,
     AVG(c.contributionScore) AS currentAvgContribution,
     // Previous period metrics
     COUNT(DISTINCT prevT) AS previousTransactions,
     SUM(prevT.amount) AS previousRevenue,
     AVG(prevC.contributionScore) AS previousAvgContribution
WITH p, currentTransactions, currentRevenue, currentAvgContribution,
     previousTransactions, previousRevenue, previousAvgContribution,
     // Calculate growth rates
     CASE 
       WHEN previousRevenue > 0 THEN ((currentRevenue - previousRevenue) / previousRevenue) * 100
       ELSE 0
     END AS revenueGrowthRate,
     CASE 
       WHEN previousTransactions > 0 THEN ((currentTransactions - previousTransactions) / toFloat(previousTransactions)) * 100
       ELSE 0
     END AS transactionGrowthRate,
     CASE 
       WHEN previousAvgContribution > 0 THEN ((currentAvgContribution - previousAvgContribution) / previousAvgContribution) * 100
       ELSE 0
     END AS contributionGrowthRate
// Get industry averages for comparison
MATCH (allPartners:Partner)-[allC:CONTRIBUTED_TO]->(allT:Transaction)
WHERE allT.timestamp >= $startDate AND allT.timestamp <= $endDate
WITH p, currentTransactions, currentRevenue, currentAvgContribution,
     previousTransactions, previousRevenue, previousAvgContribution,
     revenueGrowthRate, transactionGrowthRate, contributionGrowthRate,
     AVG(allT.amount) AS industryAvgTransaction,
     AVG(allC.contributionScore) AS industryAvgContribution
WITH p, currentTransactions, currentRevenue, currentAvgContribution,
     revenueGrowthRate, transactionGrowthRate, contributionGrowthRate,
     industryAvgTransaction, industryAvgContribution,
     CASE 
       WHEN currentTransactions > 0 THEN currentRevenue / currentTransactions
       ELSE 0
     END AS avgTransactionValue
RETURN p.id AS partnerId,
       p.name AS partnerName,
       // Current metrics
       currentTransactions AS currentTransactions,
       currentRevenue AS currentRevenue,
       avgTransactionValue AS avgTransactionValue,
       currentAvgContribution AS avgContributionScore,
       // Growth metrics
       revenueGrowthRate AS revenueGrowthPercent,
       transactionGrowthRate AS transactionGrowthPercent,
       contributionGrowthRate AS contributionGrowthPercent,
       // Benchmarking
       industryAvgTransaction AS industryAvgTransaction,
       industryAvgContribution AS industryAvgContribution,
       CASE 
         WHEN avgTransactionValue > industryAvgTransaction THEN 'ABOVE_AVERAGE'
         WHEN avgTransactionValue >= industryAvgTransaction * 0.8 THEN 'AVERAGE'
         ELSE 'BELOW_AVERAGE'
       END AS transactionValueBenchmark,
       // Performance classification
       CASE 
         WHEN revenueGrowthRate > 20 AND transactionGrowthRate > 15 THEN 'HIGH_GROWTH'
         WHEN revenueGrowthRate > 10 AND transactionGrowthRate > 5 THEN 'STEADY_GROWTH'
         WHEN revenueGrowthRate > 0 THEN 'SLOW_GROWTH'
         ELSE 'DECLINING'
       END AS performanceCategory
ORDER BY currentRevenue DESC