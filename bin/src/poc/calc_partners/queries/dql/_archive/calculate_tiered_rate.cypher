// =============================================================================
// Query: Calculate Tiered Rate
// Purpose: Calculate tiered rates for rewards based on threshold definitions and partner metrics
// =============================================================================

// Parameters:
// $ruleId: INT64 - ID of the reward rule to use for tiered calculation
// $partnerId: INT64 (optional) - Specific partner ID to calculate for
// $metricValue: DECIMAL(15,2) - The metric value to evaluate against thresholds
// $metricType: STRING - Type of metric ('transaction_amount', 'revenue', 'volume', 'tier')
// $calculateForAll: BOOLEAN (optional, default: false) - Calculate for all partners using this rule

MATCH (rr:RewardRule {id: $ruleId})
WHERE rr.type = 'tiered'

// Get all thresholds for this rule
MATCH (rr)-[:HAS_THRESHOLD]->(th:Threshold)
WHERE th.metric = $metricType

// If calculating for a specific partner, get their info
OPTIONAL MATCH (p:Partner {id: $partnerId})
WHERE $partnerId IS NOT NULL

// If calculating for all partners, get all partners using this rule
OPTIONAL MATCH (all_p:Partner)-[ar:APPLIES_RULE]->(rr)
WHERE $calculateForAll = true
  AND (ar.end_date IS NULL OR ar.end_date >= CURRENT_DATE())

// Determine which partners to process
WITH rr, th, 
  CASE 
    WHEN $partnerId IS NOT NULL THEN COLLECT(p)
    WHEN $calculateForAll = true THEN COLLECT(all_p)
    ELSE []
  END AS partners_to_process

// For each threshold, determine if the metric value falls within its range
WITH rr, th, partners_to_process,
  CASE 
    WHEN $metricValue >= th.min_value AND (th.max_value IS NULL OR $metricValue <= th.max_value) THEN th
    ELSE NULL
  END AS applicable_threshold

// Filter to get the applicable threshold (there should be only one)
WITH rr, partners_to_process, applicable_threshold
WHERE applicable_threshold IS NOT NULL

// Get all thresholds ordered by sequence to show tier structure
MATCH (rr)-[:HAS_THRESHOLD]->(all_th:Threshold)
WHERE all_th.metric = $metricType

// Calculate the tiered rate and bonus
WITH rr, partners_to_process, applicable_threshold, all_th,
  COALESCE(applicable_threshold.rate, rr.base_rate) AS applied_rate,
  COALESCE(applicable_threshold.bonus, 0) AS applied_bonus,
  CASE 
    WHEN applicable_threshold IS NOT NULL THEN applicable_threshold.sequence
    ELSE 0
  END AS tier_level

// Calculate reward amount if metric value represents a transaction amount
WITH rr, partners_to_process, applicable_threshold, all_th, applied_rate, applied_bonus, tier_level,
  CASE 
    WHEN $metricType = 'transaction_amount' THEN $metricValue * applied_rate + applied_bonus
    ELSE applied_rate
  END AS calculated_reward

RETURN 
  rr.id AS rule_id,
  rr.name AS rule_name,
  $metricType AS metric_type,
  $metricValue AS metric_value,
  tier_level AS tier_level,
  applicable_threshold.min_value AS tier_min_value,
  applicable_threshold.max_value AS tier_max_value,
  applied_rate AS applied_rate,
  applied_bonus AS applied_bonus,
  calculated_reward AS calculated_reward_amount,
  // Show all available tiers for reference
  COLLECT(DISTINCT {
    sequence: all_th.sequence,
    min_value: all_th.min_value,
    max_value: all_th.max_value,
    rate: all_th.rate,
    bonus: all_th.bonus
  }) AS all_available_tiers

ORDER BY tier_level;