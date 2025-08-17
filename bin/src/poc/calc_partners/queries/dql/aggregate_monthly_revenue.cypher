// Aggregate Monthly Revenue Query
// Purpose: Aggregate revenue data by month with breakdown by partners and segments
// Parameters: timeframe, groupBy (partner/segment/total)
// Returns: Monthly revenue aggregations with comparative analysis

MATCH (t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (t)<-[c:CONTRIBUTED_TO]-(p:Partner)
OPTIONAL MATCH (t)-[:BELONGS_TO]->(seg:Segment)
WITH t, p, seg, c,
     date({year: date(t.timestamp).year, month: date(t.timestamp).month, day: 1}) AS monthYear
WITH monthYear, p, seg,
     COUNT(t) AS monthlyTransactions,
     SUM(t.amount) AS monthlyRevenue,
     AVG(t.amount) AS avgTransactionValue,
     MIN(t.amount) AS minTransaction,
     MAX(t.amount) AS maxTransaction,
     AVG(COALESCE(c.contributionScore, 0)) AS avgContribution
// Group by the specified dimension
WITH monthYear,
     CASE COALESCE($groupBy, 'total')
       WHEN 'partner' THEN COALESCE(p.id, 'DIRECT')
       WHEN 'segment' THEN COALESCE(seg.name, 'UNASSIGNED')
       ELSE 'TOTAL'
     END AS groupingKey,
     CASE COALESCE($groupBy, 'total')
       WHEN 'partner' THEN COALESCE(p.name, 'Direct Sales')
       WHEN 'segment' THEN COALESCE(seg.name, 'Unassigned')
       ELSE 'Total Business'
     END AS groupingName,
     monthlyTransactions, monthlyRevenue, avgTransactionValue,
     minTransaction, maxTransaction, avgContribution
// Aggregate by month and grouping
WITH monthYear, groupingKey, groupingName,
     SUM(monthlyTransactions) AS totalTransactions,
     SUM(monthlyRevenue) AS totalRevenue,
     AVG(avgTransactionValue) AS avgTransactionValue,
     MIN(minTransaction) AS minTransaction,
     MAX(maxTransaction) AS maxTransaction,
     AVG(avgContribution) AS avgContribution
WITH monthYear, groupingKey, groupingName, totalTransactions, totalRevenue,
     avgTransactionValue, minTransaction, maxTransaction, avgContribution
ORDER BY monthYear, totalRevenue DESC
// Calculate month-over-month changes
WITH monthYear, groupingKey, groupingName, totalTransactions, totalRevenue,
     avgTransactionValue, avgContribution,
     LAG(totalRevenue) OVER (PARTITION BY groupingKey ORDER BY monthYear) AS previousMonthRevenue,
     LAG(totalTransactions) OVER (PARTITION BY groupingKey ORDER BY monthYear) AS previousMonthTransactions
WITH monthYear, groupingKey, groupingName, totalTransactions, totalRevenue,
     avgTransactionValue, avgContribution, previousMonthRevenue, previousMonthTransactions,
     CASE 
       WHEN previousMonthRevenue > 0 THEN ((totalRevenue - previousMonthRevenue) / previousMonthRevenue) * 100
       ELSE 0
     END AS revenueGrowthPercent,
     CASE 
       WHEN previousMonthTransactions > 0 THEN ((totalTransactions - previousMonthTransactions) / toFloat(previousMonthTransactions)) * 100
       ELSE 0
     END AS transactionGrowthPercent
// Calculate market share within each month
MATCH (allT:Transaction)
WHERE allT.timestamp >= $startDate AND allT.timestamp <= $endDate
WITH monthYear, groupingKey, groupingName, totalTransactions, totalRevenue,
     avgTransactionValue, avgContribution, revenueGrowthPercent, transactionGrowthPercent,
     date({year: date(allT.timestamp).year, month: date(allT.timestamp).month, day: 1}) AS allMonthYear,
     SUM(allT.amount) AS totalMarketRevenue
WHERE monthYear = allMonthYear
WITH monthYear, groupingKey, groupingName, totalTransactions, totalRevenue,
     avgTransactionValue, avgContribution, revenueGrowthPercent, transactionGrowthPercent,
     totalMarketRevenue,
     CASE 
       WHEN totalMarketRevenue > 0 THEN (totalRevenue / totalMarketRevenue) * 100
       ELSE 0
     END AS marketSharePercent
RETURN monthYear AS month,
       groupingKey AS groupId,
       groupingName AS groupName,
       totalTransactions AS transactionCount,
       totalRevenue AS revenue,
       avgTransactionValue AS avgTransactionValue,
       avgContribution AS avgContributionScore,
       revenueGrowthPercent AS revenueGrowthPercent,
       transactionGrowthPercent AS transactionGrowthPercent,
       marketSharePercent AS marketSharePercent,
       CASE 
         WHEN revenueGrowthPercent > 20 THEN 'HIGH_GROWTH'
         WHEN revenueGrowthPercent > 5 THEN 'STEADY_GROWTH'
         WHEN revenueGrowthPercent > -5 THEN 'STABLE'
         WHEN revenueGrowthPercent > -20 THEN 'DECLINING'
         ELSE 'SIGNIFICANT_DECLINE'
       END AS growthCategory,
       // Running totals
       SUM(totalRevenue) OVER (PARTITION BY groupingKey ORDER BY monthYear) AS cumulativeRevenue,
       SUM(totalTransactions) OVER (PARTITION BY groupingKey ORDER BY monthYear) AS cumulativeTransactions
ORDER BY monthYear, totalRevenue DESC