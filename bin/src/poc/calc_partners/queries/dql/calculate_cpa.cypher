// Calculate Cost Per Acquisition (CPA) Query
// Purpose: Calculate the cost to acquire customers through different partners
// Parameters: partnerId, timeframe, campaignId (optional)
// Returns: CPA metrics and acquisition efficiency

MATCH (p:Partner {id: $partnerId})
OPTIONAL MATCH (p)-[:ACQUIRED]->(c:Customer)
WHERE c.acquisitionDate >= $startDate AND c.acquisitionDate <= $endDate
OPTIONAL MATCH (p)-[:INCURRED_COST]->(cost:MarketingCost)
WHERE cost.timestamp >= $startDate AND cost.timestamp <= $endDate
OPTIONAL MATCH (p)-[:RAN_CAMPAIGN]->(camp:Campaign {id: $campaignId})-[:INCURRED_COST]->(campCost:CampaignCost)
WHERE campCost.timestamp >= $startDate AND campCost.timestamp <= $endDate
WITH p,
     COUNT(DISTINCT c) AS customersAcquired,
     SUM(cost.amount) AS totalMarketingCosts,
     SUM(campCost.amount) AS campaignCosts
WITH p, customersAcquired, totalMarketingCosts, campaignCosts,
     (totalMarketingCosts + COALESCE(campaignCosts, 0)) AS totalAcquisitionCosts
WITH p, customersAcquired, totalAcquisitionCosts,
     CASE 
       WHEN customersAcquired > 0 THEN totalAcquisitionCosts / customersAcquired
       ELSE 0
     END AS costPerAcquisition
// Calculate industry benchmark comparison
MATCH (allPartners:Partner)-[:ACQUIRED]->(allCustomers:Customer)
WHERE allCustomers.acquisitionDate >= $startDate AND allCustomers.acquisitionDate <= $endDate
OPTIONAL MATCH (allPartners)-[:INCURRED_COST]->(allCosts:MarketingCost)
WHERE allCosts.timestamp >= $startDate AND allCosts.timestamp <= $endDate
WITH p, customersAcquired, totalAcquisitionCosts, costPerAcquisition,
     COUNT(DISTINCT allCustomers) AS totalCustomersAcquired,
     SUM(allCosts.amount) AS totalIndustryCosts
WITH p, customersAcquired, totalAcquisitionCosts, costPerAcquisition,
     CASE 
       WHEN totalCustomersAcquired > 0 THEN totalIndustryCosts / totalCustomersAcquired
       ELSE 0
     END AS industryAvgCPA
RETURN p.id AS partnerId,
       p.name AS partnerName,
       customersAcquired AS customersAcquired,
       totalAcquisitionCosts AS totalCosts,
       costPerAcquisition AS costPerAcquisition,
       industryAvgCPA AS industryAverage,
       CASE 
         WHEN costPerAcquisition < industryAvgCPA THEN 'EFFICIENT'
         WHEN costPerAcquisition <= industryAvgCPA * 1.2 THEN 'AVERAGE'
         ELSE 'EXPENSIVE'
       END AS acquisitionEfficiency