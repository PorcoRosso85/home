// Calculate Churn Rate Query
// Purpose: Calculate customer churn rate for partners and overall business
// Parameters: partnerId (optional), timeframe, churnPeriod
// Returns: Churn metrics and retention analysis

MATCH (c:Customer)
WHERE c.acquisitionDate <= $endDate
OPTIONAL MATCH (c)-[:ACQUIRED_BY]->(p:Partner {id: $partnerId})
OPTIONAL MATCH (c)-[pur:PURCHASED]->(t:Transaction)
WITH c, p,
     MAX(t.timestamp) AS lastActivity,
     COUNT(t) AS totalTransactions
WITH c, p, lastActivity, totalTransactions,
     CASE 
       WHEN lastActivity IS NULL THEN true
       WHEN duration.between(lastActivity, $endDate).days > COALESCE($churnPeriod, 90) THEN true
       ELSE false
     END AS isChurned
WITH p,
     COUNT(c) AS totalCustomers,
     SUM(CASE WHEN isChurned THEN 1 ELSE 0 END) AS churnedCustomers,
     SUM(CASE WHEN NOT isChurned THEN 1 ELSE 0 END) AS activeCustomers
WITH p, totalCustomers, churnedCustomers, activeCustomers,
     CASE 
       WHEN totalCustomers > 0 THEN (churnedCustomers * 100.0) / totalCustomers
       ELSE 0
     END AS churnRate,
     CASE 
       WHEN totalCustomers > 0 THEN (activeCustomers * 100.0) / totalCustomers
       ELSE 0
     END AS retentionRate
// Calculate period-over-period comparison
MATCH (prevC:Customer)
WHERE prevC.acquisitionDate <= date.sub($startDate, duration({months: 1}))
OPTIONAL MATCH (prevC)-[:ACQUIRED_BY]->(prevP:Partner {id: $partnerId})
OPTIONAL MATCH (prevC)-[prevPur:PURCHASED]->(prevT:Transaction)
WITH p, totalCustomers, churnedCustomers, activeCustomers, churnRate, retentionRate,
     prevC, prevP,
     MAX(prevT.timestamp) AS prevLastActivity
WITH p, totalCustomers, churnedCustomers, activeCustomers, churnRate, retentionRate,
     COUNT(prevC) AS prevTotalCustomers,
     SUM(CASE 
       WHEN prevLastActivity IS NULL OR duration.between(prevLastActivity, $startDate).days > COALESCE($churnPeriod, 90) 
       THEN 1 ELSE 0 END) AS prevChurnedCustomers
WITH p, totalCustomers, churnedCustomers, activeCustomers, churnRate, retentionRate,
     prevTotalCustomers,
     CASE 
       WHEN prevTotalCustomers > 0 THEN (prevChurnedCustomers * 100.0) / prevTotalCustomers
       ELSE 0
     END AS prevChurnRate
RETURN COALESCE(p.id, 'ALL_PARTNERS') AS partnerId,
       COALESCE(p.name, 'All Partners') AS partnerName,
       totalCustomers AS totalCustomers,
       activeCustomers AS activeCustomers,
       churnedCustomers AS churnedCustomers,
       churnRate AS churnRatePercent,
       retentionRate AS retentionRatePercent,
       prevChurnRate AS previousPeriodChurnRate,
       (churnRate - prevChurnRate) AS churnRateChange