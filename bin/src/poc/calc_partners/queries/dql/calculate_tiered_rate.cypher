// Calculate Tiered Rate Query
// Purpose: Calculate tiered reward rates based on partner performance and volume
// Parameters: partnerId, evaluationPeriod
// Returns: Current tier and applicable rates

MATCH (p:Partner {id: $partnerId})-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[:HAS_TIER_STRUCTURE]->(ts:TierStructure)
WITH p, ts,
     SUM(t.amount) AS totalVolume,
     COUNT(t) AS transactionCount,
     AVG(c.contributionScore) AS avgContribution
WITH p, ts, totalVolume, transactionCount, avgContribution,
     CASE
       WHEN totalVolume >= ts.platinumThreshold AND avgContribution >= 0.8 THEN 'PLATINUM'
       WHEN totalVolume >= ts.goldThreshold AND avgContribution >= 0.6 THEN 'GOLD'
       WHEN totalVolume >= ts.silverThreshold AND avgContribution >= 0.4 THEN 'SILVER'
       ELSE 'BRONZE'
     END AS currentTier
WITH p, ts, totalVolume, transactionCount, avgContribution, currentTier,
     CASE currentTier
       WHEN 'PLATINUM' THEN ts.platinumRate
       WHEN 'GOLD' THEN ts.goldRate
       WHEN 'SILVER' THEN ts.silverRate
       ELSE ts.bronzeRate
     END AS applicableRate
RETURN p.id AS partnerId,
       p.name AS partnerName,
       currentTier AS tier,
       applicableRate AS rate,
       totalVolume AS volumeGenerated,
       transactionCount AS transactionCount,
       avgContribution AS averageContribution