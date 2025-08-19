// =============================================================================
// Query: Calculate Partner Reward
// Purpose: Calculate rewards for a specific partner based on their transactions and applicable reward rules
// =============================================================================

// Parameters:
// $partnerId: INT64 - ID of the partner to calculate rewards for
// $transactionId: INT64 (optional) - Specific transaction ID to calculate reward for
// $ruleId: INT64 (optional) - Specific rule ID to use for calculation
// $periodStart: DATE (optional) - Start date for reward calculation period
// $periodEnd: DATE (optional) - End date for reward calculation period

MATCH (p:Partner {id: $partnerId})
OPTIONAL MATCH (p)-[ar:APPLIES_RULE]->(rr:RewardRule)
WHERE (ar.end_date IS NULL OR ar.end_date >= CURRENT_DATE())
  AND ($ruleId IS NULL OR rr.id = $ruleId)

OPTIONAL MATCH (t:Transaction {partner_id: $partnerId})
WHERE ($transactionId IS NULL OR t.id = $transactionId)
  AND ($periodStart IS NULL OR t.transaction_date >= $periodStart)
  AND ($periodEnd IS NULL OR t.transaction_date <= $periodEnd)
  AND t.status = 'confirmed'

OPTIONAL MATCH (rr)-[:HAS_THRESHOLD]->(th:Threshold)
WHERE th.metric = 'transaction_amount'
  AND t.amount >= th.min_value
  AND (th.max_value IS NULL OR t.amount <= th.max_value)

WITH p, rr, t, th,
  CASE 
    WHEN rr.type = 'fixed' THEN rr.base_amount
    WHEN rr.type = 'percentage' THEN t.amount * rr.base_rate
    WHEN rr.type = 'tiered' AND th IS NOT NULL THEN 
      CASE 
        WHEN th.rate IS NOT NULL THEN t.amount * th.rate + COALESCE(th.bonus, 0)
        ELSE rr.base_amount
      END
    ELSE 0
  END AS calculated_reward

RETURN 
  p.id AS partner_id,
  p.code AS partner_code,
  p.name AS partner_name,
  rr.id AS rule_id,
  rr.name AS rule_name,
  rr.type AS rule_type,
  t.id AS transaction_id,
  t.amount AS transaction_amount,
  calculated_reward AS reward_amount,
  th.sequence AS threshold_tier,
  CASE 
    WHEN calculated_reward > 0 THEN 'calculated'
    ELSE 'no_reward'
  END AS calculation_status

ORDER BY rr.id, t.transaction_date DESC;