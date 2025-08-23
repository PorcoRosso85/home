// Cashflow Projection Query
// Projects future cashflows based on partner performance trends
// Parameters: $quarterCount

WITH $quarterCount AS quarterCount

// Get all partners and their current metrics
MATCH (p:Entity {type: 'partner'})
OPTIONAL MATCH (p)-[:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH p, COUNT(c) AS customerCount, AVG(c.ltv) AS avgLtv, quarterCount

// Generate quarterly projections
UNWIND range(1, quarterCount) AS quarter
WITH p, quarter, customerCount, avgLtv,
     // Assume 5% quarterly growth
     customerCount * POWER(1.05, quarter) AS projectedCustomers,
     // Calculate quarterly revenue (25% of annual LTV)
     customerCount * avgLtv * 0.25 * POWER(1.05, quarter) AS quarterlyRevenue,
     // Calculate reward payments (10% of revenue)
     customerCount * avgLtv * 0.25 * POWER(1.05, quarter) * 0.10 AS rewardPayment

// Aggregate by quarter
WITH quarter,
     SUM(quarterlyRevenue) AS totalRevenue,
     SUM(rewardPayment) AS totalRewards,
     SUM(projectedCustomers) AS totalCustomers

RETURN 
  'Q' || quarter AS period,
  ROUND(totalRevenue) AS revenue,
  ROUND(totalRewards) AS rewards,
  ROUND(totalRevenue - totalRewards) AS netIncome,
  ROUND(totalCustomers) AS customerBase,
  ROUND((totalRevenue - totalRewards) / totalRevenue * 100) AS profitMarginPercent
ORDER BY quarter