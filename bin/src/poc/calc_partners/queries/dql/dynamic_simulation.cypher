// Dynamic Partner Simulation Query
// Simulates partner growth over time with various scenarios
// Parameters: $partnerId, $monthsToSimulate, $growthRate, $churnRate

WITH $partnerId AS partnerId,
     $monthsToSimulate AS monthsToSimulate,
     $growthRate AS growthRate,
     $churnRate AS churnRate

// Get current partner state
MATCH (p:Entity {id: partnerId, type: 'partner'})
OPTIONAL MATCH (p)-[:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH p, COUNT(c) AS currentCustomers, 
     AVG(c.ltv) AS avgCustomerLtv,
     monthsToSimulate, growthRate, churnRate

// Simulate monthly growth
UNWIND range(1, monthsToSimulate) AS month
WITH p, month, currentCustomers, avgCustomerLtv, growthRate, churnRate,
     // Calculate cumulative customers with growth and churn
     currentCustomers * POWER(1 + growthRate - churnRate, month) AS projectedCustomers,
     // Calculate cumulative revenue
     currentCustomers * avgCustomerLtv * POWER(1 + growthRate - churnRate, month) AS projectedRevenue

// Calculate monthly metrics
WITH p, month, 
     ROUND(projectedCustomers) AS customerCount,
     ROUND(projectedRevenue) AS totalRevenue,
     ROUND(projectedRevenue / projectedCustomers) AS avgRevenuePerCustomer,
     currentCustomers

RETURN 
  p.name AS partnerName,
  month,
  customerCount,
  totalRevenue,
  avgRevenuePerCustomer,
  CASE 
    WHEN customerCount > currentCustomers * 2 THEN 'High Growth'
    WHEN customerCount > currentCustomers * 1.5 THEN 'Moderate Growth'
    WHEN customerCount > currentCustomers THEN 'Stable Growth'
    ELSE 'Declining'
  END AS growthStatus
ORDER BY month