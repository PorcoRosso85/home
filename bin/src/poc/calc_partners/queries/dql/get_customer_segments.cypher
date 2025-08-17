// Get Customer Segments Query
// Purpose: Analyze customer segments and their characteristics for partner-driven acquisition
// Parameters: timeframe, segmentationType (value/frequency/recency)
// Returns: Customer segment analysis with partner attribution

MATCH (c:Customer)
OPTIONAL MATCH (c)-[:ACQUIRED_BY]->(p:Partner)
OPTIONAL MATCH (c)-[pur:PURCHASED]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
WITH c, p,
     COUNT(pur) AS transactionCount,
     SUM(t.amount) AS totalSpent,
     AVG(t.amount) AS avgOrderValue,
     MIN(t.timestamp) AS firstPurchase,
     MAX(t.timestamp) AS lastPurchase,
     CASE 
       WHEN COUNT(pur) = 0 THEN duration.between(c.acquisitionDate, $endDate).days
       ELSE duration.between(MAX(t.timestamp), $endDate).days
     END AS daysSinceLastActivity
WITH c, p, transactionCount, totalSpent, avgOrderValue, firstPurchase, lastPurchase, daysSinceLastActivity,
     CASE 
       WHEN firstPurchase IS NOT NULL AND lastPurchase IS NOT NULL THEN duration.between(firstPurchase, lastPurchase).days
       ELSE 0
     END AS customerLifespanDays
// Calculate RFM scores (Recency, Frequency, Monetary)
WITH c, p, transactionCount, totalSpent, avgOrderValue, daysSinceLastActivity, customerLifespanDays,
     // Recency Score (1-5, 5 = most recent)
     CASE 
       WHEN daysSinceLastActivity <= 30 THEN 5
       WHEN daysSinceLastActivity <= 60 THEN 4
       WHEN daysSinceLastActivity <= 90 THEN 3
       WHEN daysSinceLastActivity <= 180 THEN 2
       ELSE 1
     END AS recencyScore,
     // Frequency Score (1-5, 5 = most frequent)
     CASE 
       WHEN transactionCount >= 20 THEN 5
       WHEN transactionCount >= 10 THEN 4
       WHEN transactionCount >= 5 THEN 3
       WHEN transactionCount >= 2 THEN 2
       ELSE 1
     END AS frequencyScore,
     // Monetary Score (1-5, 5 = highest value)
     CASE 
       WHEN totalSpent >= 10000 THEN 5
       WHEN totalSpent >= 5000 THEN 4
       WHEN totalSpent >= 2000 THEN 3
       WHEN totalSpent >= 500 THEN 2
       ELSE 1
     END AS monetaryScore
// Create segment classifications
WITH c, p, transactionCount, totalSpent, avgOrderValue, daysSinceLastActivity,
     customerLifespanDays, recencyScore, frequencyScore, monetaryScore,
     // Overall RFM segment
     CASE 
       WHEN recencyScore >= 4 AND frequencyScore >= 4 AND monetaryScore >= 4 THEN 'CHAMPION'
       WHEN recencyScore >= 3 AND frequencyScore >= 3 AND monetaryScore >= 4 THEN 'LOYAL_CUSTOMER'
       WHEN recencyScore >= 4 AND frequencyScore <= 2 AND monetaryScore >= 3 THEN 'POTENTIAL_LOYALIST'
       WHEN recencyScore >= 4 AND frequencyScore <= 2 AND monetaryScore <= 2 THEN 'NEW_CUSTOMER'
       WHEN recencyScore >= 3 AND frequencyScore >= 3 AND monetaryScore <= 3 THEN 'PROMISING'
       WHEN recencyScore <= 2 AND frequencyScore >= 3 AND monetaryScore >= 3 THEN 'NEED_ATTENTION'
       WHEN recencyScore <= 2 AND frequencyScore >= 3 AND monetaryScore <= 2 THEN 'ABOUT_TO_SLEEP'
       WHEN recencyScore >= 3 AND frequencyScore <= 2 AND monetaryScore <= 2 THEN 'AT_RISK'
       WHEN recencyScore <= 2 AND frequencyScore <= 2 AND monetaryScore >= 3 THEN 'CANNOT_LOSE_THEM'
       WHEN recencyScore <= 2 AND frequencyScore <= 2 AND monetaryScore <= 2 THEN 'HIBERNATING'
       ELSE 'OTHERS'
     END AS rfmSegment,
     // Value-based segment
     CASE 
       WHEN totalSpent >= 10000 THEN 'HIGH_VALUE'
       WHEN totalSpent >= 2000 THEN 'MEDIUM_VALUE'
       WHEN totalSpent >= 500 THEN 'LOW_VALUE'
       ELSE 'MINIMAL_VALUE'
     END AS valueSegment,
     // Frequency-based segment
     CASE 
       WHEN transactionCount >= 15 THEN 'VERY_FREQUENT'
       WHEN transactionCount >= 8 THEN 'FREQUENT'
       WHEN transactionCount >= 3 THEN 'OCCASIONAL'
       WHEN transactionCount >= 1 THEN 'RARE'
       ELSE 'INACTIVE'
     END AS frequencySegment
// Aggregate by segments
WITH CASE COALESCE($segmentationType, 'rfm')
       WHEN 'value' THEN valueSegment
       WHEN 'frequency' THEN frequencySegment
       WHEN 'recency' THEN 
         CASE 
           WHEN recencyScore >= 4 THEN 'RECENT'
           WHEN recencyScore >= 3 THEN 'MODERATE'
           ELSE 'DISTANT'
         END
       ELSE rfmSegment
     END AS segmentName,
     p,
     c, totalSpent, transactionCount, avgOrderValue, daysSinceLastActivity
WITH segmentName,
     COUNT(DISTINCT c) AS customerCount,
     SUM(totalSpent) AS segmentRevenue,
     AVG(totalSpent) AS avgCustomerValue,
     AVG(transactionCount) AS avgTransactionCount,
     AVG(avgOrderValue) AS avgOrderValue,
     AVG(daysSinceLastActivity) AS avgDaysSinceActivity,
     // Partner attribution
     COUNT(DISTINCT p) AS partnerCount,
     COLLECT(DISTINCT p.name)[0..5] AS topPartners  // Top 5 partners
WITH segmentName, customerCount, segmentRevenue, avgCustomerValue,
     avgTransactionCount, avgOrderValue, avgDaysSinceActivity, partnerCount, topPartners,
     // Calculate segment metrics
     CASE 
       WHEN customerCount > 0 THEN segmentRevenue / customerCount
       ELSE 0
     END AS revenuePerCustomer
// Get total market for percentage calculations
MATCH (allC:Customer)
OPTIONAL MATCH (allC)-[allPur:PURCHASED]->(allT:Transaction)
WHERE allT.timestamp >= $startDate AND allT.timestamp <= $endDate
WITH segmentName, customerCount, segmentRevenue, avgCustomerValue,
     avgTransactionCount, avgOrderValue, avgDaysSinceActivity, partnerCount, topPartners, revenuePerCustomer,
     COUNT(DISTINCT allC) AS totalCustomers,
     SUM(allT.amount) AS totalRevenue
WITH segmentName, customerCount, segmentRevenue, avgCustomerValue,
     avgTransactionCount, avgOrderValue, avgDaysSinceActivity, partnerCount, topPartners, revenuePerCustomer,
     CASE 
       WHEN totalCustomers > 0 THEN (customerCount / toFloat(totalCustomers)) * 100
       ELSE 0
     END AS customerPercentage,
     CASE 
       WHEN totalRevenue > 0 THEN (segmentRevenue / totalRevenue) * 100
       ELSE 0
     END AS revenuePercentage
RETURN segmentName AS segment,
       customerCount AS customerCount,
       customerPercentage AS customerPercentage,
       segmentRevenue AS revenue,
       revenuePercentage AS revenuePercentage,
       avgCustomerValue AS avgCustomerValue,
       revenuePerCustomer AS revenuePerCustomer,
       avgTransactionCount AS avgTransactionCount,
       avgOrderValue AS avgOrderValue,
       avgDaysSinceActivity AS avgDaysSinceLastActivity,
       partnerCount AS contributingPartners,
       topPartners AS topContributingPartners,
       // Segment health indicators
       CASE 
         WHEN avgDaysSinceActivity <= 30 THEN 'ACTIVE'
         WHEN avgDaysSinceActivity <= 90 THEN 'MODERATELY_ACTIVE'
         ELSE 'INACTIVE'
       END AS activityLevel,
       CASE 
         WHEN revenuePercentage > 30 THEN 'CRITICAL'
         WHEN revenuePercentage > 15 THEN 'IMPORTANT'
         WHEN revenuePercentage > 5 THEN 'SIGNIFICANT'
         ELSE 'MINOR'
       END AS businessImpact
ORDER BY segmentRevenue DESC