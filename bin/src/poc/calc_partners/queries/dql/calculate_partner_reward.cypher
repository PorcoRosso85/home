// Calculate Partner Reward Query
// Purpose: Calculate reward amount for a specific partner based on their contribution
// Parameters: partnerId, transactionId, rewardType
// Returns: Partner reward calculation with breakdown

MATCH (p:Partner {id: $partnerId})-[r:CONTRIBUTED_TO]->(t:Transaction {id: $transactionId})
OPTIONAL MATCH (p)-[:HAS_REWARD_STRUCTURE]->(rs:RewardStructure)
WITH p, t, r, rs,
     CASE rs.type
       WHEN 'percentage' THEN t.amount * rs.rate
       WHEN 'fixed' THEN rs.fixedAmount
       WHEN 'tiered' THEN 
         CASE 
           WHEN t.amount >= rs.tier3Threshold THEN t.amount * rs.tier3Rate
           WHEN t.amount >= rs.tier2Threshold THEN t.amount * rs.tier2Rate
           ELSE t.amount * rs.tier1Rate
         END
       ELSE 0
     END AS calculatedReward
RETURN p.id AS partnerId,
       p.name AS partnerName,
       t.id AS transactionId,
       t.amount AS transactionAmount,
       rs.type AS rewardType,
       calculatedReward AS rewardAmount,
       r.contributionScore AS contributionScore,
       calculatedReward * r.contributionScore AS finalReward