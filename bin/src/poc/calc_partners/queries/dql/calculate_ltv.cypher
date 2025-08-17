// Calculate Customer Lifetime Value (LTV) Query
// Purpose: Calculate the predicted lifetime value of customers acquired through partners
// Parameters: customerId, partnerId (optional), predictionPeriod
// Returns: LTV calculation and contributing factors

MATCH (c:Customer {id: $customerId})
OPTIONAL MATCH (c)-[:ACQUIRED_BY]->(p:Partner {id: $partnerId})
OPTIONAL MATCH (c)-[pur:PURCHASED]->(t:Transaction)
WHERE t.timestamp >= $startDate
WITH c, p,
     COUNT(pur) AS totalPurchases,
     SUM(t.amount) AS totalSpent,
     AVG(t.amount) AS avgOrderValue,
     MIN(t.timestamp) AS firstPurchase,
     MAX(t.timestamp) AS lastPurchase
WITH c, p, totalPurchases, totalSpent, avgOrderValue, firstPurchase, lastPurchase,
     duration.between(firstPurchase, lastPurchase).days AS customerLifespanDays
WITH c, p, totalPurchases, totalSpent, avgOrderValue, customerLifespanDays,
     CASE 
       WHEN customerLifespanDays > 0 THEN totalPurchases / (customerLifespanDays / 30.0)
       ELSE 0
     END AS avgMonthlyPurchases,
     CASE 
       WHEN customerLifespanDays > 0 THEN totalSpent / (customerLifespanDays / 30.0)
       ELSE 0
     END AS avgMonthlySpend
WITH c, p, totalPurchases, totalSpent, avgOrderValue, customerLifespanDays,
     avgMonthlyPurchases, avgMonthlySpend,
     COALESCE($predictionPeriod, 24) AS predictionMonths
WITH c, p, totalPurchases, totalSpent, avgOrderValue, customerLifespanDays,
     avgMonthlyPurchases, avgMonthlySpend, predictionMonths,
     (avgMonthlySpend * predictionMonths) AS projectedLTV
RETURN c.id AS customerId,
       c.name AS customerName,
       p.id AS acquisitionPartnerId,
       p.name AS acquisitionPartnerName,
       totalPurchases AS totalPurchases,
       totalSpent AS totalSpent,
       avgOrderValue AS averageOrderValue,
       customerLifespanDays AS lifespanDays,
       avgMonthlyPurchases AS avgMonthlyPurchases,
       avgMonthlySpend AS avgMonthlySpend,
       projectedLTV AS projectedLifetimeValue,
       predictionMonths AS projectionPeriodMonths