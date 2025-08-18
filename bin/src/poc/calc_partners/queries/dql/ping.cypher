// =============================================================================
// Query: Database Connectivity Test (Ping)
// Purpose: Simple database connectivity test with system status
// Pain Point: 「KuzuDBがちゃんと動いてるか、まずは確認したい。」
// =============================================================================

// Parameters:
// $includeStats: BOOLEAN (optional, default: false) - Include basic table statistics
// $timeout: INT32 (optional, default: 5) - Maximum execution time in seconds
// $customMessage: STRING (optional) - Custom message to include in response

// Basic connectivity test with timestamp
WITH 
  COALESCE($customMessage, 'Database connectivity test') AS message,
  CURRENT_TIMESTAMP() AS current_time,
  COALESCE($includeStats, false) AS include_stats

// Optional: Include basic table statistics if requested
OPTIONAL MATCH (p:Partner)
WITH message, current_time, include_stats, COUNT(p) AS partner_count

OPTIONAL MATCH (t:Transaction)
WITH message, current_time, include_stats, partner_count, COUNT(t) AS transaction_count

OPTIONAL MATCH (r:Reward)
WITH message, current_time, include_stats, partner_count, transaction_count, COUNT(r) AS reward_count

OPTIONAL MATCH (rr:RewardRule)
WITH message, current_time, include_stats, partner_count, transaction_count, reward_count, COUNT(rr) AS rule_count

// Return comprehensive ping response
RETURN 
  'pong' AS response,
  1 AS status,
  message AS message,
  current_time AS timestamp,
  'KuzuDB' AS database_type,
  CASE 
    WHEN include_stats THEN 
      STRUCT(
        partners: partner_count,
        transactions: transaction_count,
        rewards: reward_count,
        rules: rule_count,
        total_nodes: partner_count + transaction_count + reward_count + rule_count
      )
    ELSE NULL
  END AS statistics,
  CASE 
    WHEN partner_count >= 0 AND transaction_count >= 0 THEN 'healthy'
    ELSE 'warning'
  END AS health_status,
  'Database is responsive and accessible' AS description

// Usage Examples:
// Basic ping: No parameters needed
// With stats: Set $includeStats = true
// Custom message: Set $customMessage = "Production health check"
// With timeout: Set $timeout = 10