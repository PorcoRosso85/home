// Get Revenue Timeline Query
// Purpose: Generate revenue timeline with trends and forecasting data
// Parameters: timeframe, granularity (monthly/weekly/daily), partnerId (optional)
// Returns: Time-series revenue data with trend analysis

MATCH (t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (t)<-[:CONTRIBUTED_TO]-(p:Partner {id: $partnerId})
WHERE $partnerId IS NULL OR p.id = $partnerId
WITH t, p,
     CASE COALESCE($granularity, 'monthly')
       WHEN 'daily' THEN date(t.timestamp)
       WHEN 'weekly' THEN date(t.timestamp) - duration({days: date(t.timestamp).dayOfWeek - 1})
       ELSE date({year: date(t.timestamp).year, month: date(t.timestamp).month, day: 1})
     END AS timePeriod
WITH timePeriod,
     COUNT(t) AS transactionCount,
     SUM(t.amount) AS periodRevenue,
     AVG(t.amount) AS avgTransactionValue,
     MIN(t.amount) AS minTransaction,
     MAX(t.amount) AS maxTransaction
WITH timePeriod, transactionCount, periodRevenue, avgTransactionValue, minTransaction, maxTransaction
ORDER BY timePeriod
WITH COLLECT({
  period: timePeriod,
  revenue: periodRevenue,
  transactions: transactionCount,
  avgValue: avgTransactionValue,
  minValue: minTransaction,
  maxValue: maxTransaction
}) AS timelineData
// Calculate moving averages and trends
UNWIND range(0, size(timelineData) - 1) AS i
WITH timelineData, i,
     timelineData[i] AS currentPeriod,
     CASE 
       WHEN i >= 2 THEN 
         (timelineData[i].revenue + timelineData[i-1].revenue + timelineData[i-2].revenue) / 3.0
       WHEN i >= 1 THEN 
         (timelineData[i].revenue + timelineData[i-1].revenue) / 2.0
       ELSE timelineData[i].revenue
     END AS movingAvg3Period,
     CASE 
       WHEN i > 0 THEN 
         ((timelineData[i].revenue - timelineData[i-1].revenue) / timelineData[i-1].revenue) * 100
       ELSE 0
     END AS periodGrowthRate
// Calculate trend direction
WITH timelineData, i, currentPeriod, movingAvg3Period, periodGrowthRate,
     CASE 
       WHEN i >= 2 THEN
         CASE 
           WHEN timelineData[i].revenue > timelineData[i-1].revenue AND timelineData[i-1].revenue > timelineData[i-2].revenue THEN 'UPWARD'
           WHEN timelineData[i].revenue < timelineData[i-1].revenue AND timelineData[i-1].revenue < timelineData[i-2].revenue THEN 'DOWNWARD'
           ELSE 'SIDEWAYS'
         END
       ELSE 'INSUFFICIENT_DATA'
     END AS trendDirection
RETURN currentPeriod.period AS timePeriod,
       currentPeriod.revenue AS revenue,
       currentPeriod.transactions AS transactionCount,
       currentPeriod.avgValue AS avgTransactionValue,
       currentPeriod.minValue AS minTransactionValue,
       currentPeriod.maxValue AS maxTransactionValue,
       movingAvg3Period AS movingAverage,
       periodGrowthRate AS growthRatePercent,
       trendDirection AS trendDirection,
       // Forecasting hint (simple linear projection)
       CASE 
         WHEN periodGrowthRate > 0 THEN currentPeriod.revenue * (1 + periodGrowthRate/100)
         ELSE currentPeriod.revenue
       END AS simpleProjection
ORDER BY timePeriod