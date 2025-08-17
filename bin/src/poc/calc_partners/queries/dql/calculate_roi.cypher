// Calculate ROI Query
// Purpose: Calculate Return on Investment for partner acquisition and management
// Parameters: partnerId, timeframe, acquisitionCost
// Returns: ROI metrics and profitability analysis

MATCH (p:Partner {id: $partnerId})
OPTIONAL MATCH (p)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[:INCURRED_COST]->(cost:Cost)
WHERE cost.timestamp >= $startDate AND cost.timestamp <= $endDate
WITH p,
     COALESCE(SUM(t.amount), 0) AS totalRevenue,
     COALESCE(SUM(cost.amount), 0) AS operationalCosts,
     COALESCE($acquisitionCost, p.acquisitionCost, 0) AS acquisitionCost
WITH p, totalRevenue, operationalCosts, acquisitionCost,
     (operationalCosts + acquisitionCost) AS totalInvestment,
     (totalRevenue - operationalCosts - acquisitionCost) AS netProfit
WITH p, totalRevenue, operationalCosts, acquisitionCost, totalInvestment, netProfit,
     CASE 
       WHEN totalInvestment > 0 THEN (netProfit / totalInvestment) * 100
       ELSE 0
     END AS roiPercentage
RETURN p.id AS partnerId,
       p.name AS partnerName,
       totalRevenue AS revenueGenerated,
       operationalCosts AS operationalCosts,
       acquisitionCost AS acquisitionCost,
       totalInvestment AS totalInvestment,
       netProfit AS netProfit,
       roiPercentage AS roiPercentage,
       CASE 
         WHEN roiPercentage > 100 THEN 'HIGHLY_PROFITABLE'
         WHEN roiPercentage > 50 THEN 'PROFITABLE'
         WHEN roiPercentage > 0 THEN 'MARGINALLY_PROFITABLE'
         ELSE 'UNPROFITABLE'
       END AS profitabilityStatus