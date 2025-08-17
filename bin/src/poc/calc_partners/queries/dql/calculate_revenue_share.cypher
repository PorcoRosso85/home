// Calculate Revenue Share Query
// Purpose: Calculate revenue sharing between partners based on their contribution levels
// Parameters: partnerId, timeframe (optional), revenuePoolId
// Returns: Revenue share calculation and distribution

MATCH (p:Partner {id: $partnerId})-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (rp:RevenuePool {id: $revenuePoolId})
WITH p, 
     SUM(t.amount * c.contributionScore) AS partnerContribution,
     SUM(t.amount) AS totalRevenue,
     rp
MATCH (allPartners:Partner)-[ac:CONTRIBUTED_TO]->(at:Transaction)
WHERE at.timestamp >= $startDate AND at.timestamp <= $endDate
WITH p, partnerContribution, totalRevenue, rp,
     SUM(at.amount * ac.contributionScore) AS totalContributions
WITH p, partnerContribution, totalRevenue, rp, totalContributions,
     (partnerContribution / totalContributions) AS sharePercentage
RETURN p.id AS partnerId,
       p.name AS partnerName,
       partnerContribution AS partnerContribution,
       totalContributions AS totalContributions,
       sharePercentage AS sharePercentage,
       (rp.totalAmount * sharePercentage) AS revenueShare,
       totalRevenue AS periodRevenue