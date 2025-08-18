// =============================================================================
// Query: Get Partner Metrics Dashboard
// Purpose: Comprehensive partner performance metrics for real-time dashboard display
// Parameters:
//   $partnerId (optional): Specific partner ID to focus on [string]
//   $tierFilter (optional): Filter by partner tier ('bronze', 'silver', 'gold', 'platinum') [string]
//   $startDate (optional): Start date for metrics calculation (YYYY-MM-DD) [string]
//   $endDate (optional): End date for metrics calculation (YYYY-MM-DD) [string]
//   $topN (optional): Number of top performers to return (default: 10) [integer]
//   $includeInactive (optional): Include inactive partners (default: false) [boolean]
//   $sortBy (optional): Sort criteria ('performance', 'revenue', 'activity', 'tier') [string]
//   $realtime (optional): Enable real-time mode with current timestamps (default: true) [boolean]
// Returns: Partner metrics optimized for real-time dashboard display with UI-ready formatting
// Usage Example: 
//   CALL { ... } WITH { partnerId: "P001", tierFilter: "gold", topN: 20, realtime: true }
// =============================================================================

// Main partner metrics query with performance indicators
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(t:Transaction)
OPTIONAL MATCH (p)<-[:REFERS]-(referral:Partner)
OPTIONAL MATCH (p)-[:REFERS]->(referred:Partner)
OPTIONAL MATCH (p)-[ar:APPLIES_RULE]->(rr:RewardRule)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(r:Reward)

// Apply filters with parameter validation and real-time support
WHERE 
  ($partnerId IS NULL OR p.id = $partnerId)
  AND ($tierFilter IS NULL OR p.tier = $tierFilter)
  AND ($startDate IS NULL OR t.transaction_date >= date($startDate))
  AND ($endDate IS NULL OR t.transaction_date <= date($endDate))
  AND (ar.end_date IS NULL OR ar.end_date >= CASE WHEN $realtime THEN date() ELSE date('2024-01-01') END)
  AND (NOT coalesce($includeInactive, false) IMPLIES 
       (t.transaction_date IS NULL OR t.transaction_date >= date_sub(date(), duration({months: 6}))))
  AND (t.status IS NULL OR t.status IN ['confirmed', 'pending', 'completed'])

// Aggregate metrics by partner
WITH p,
     count(DISTINCT t) as total_transactions,
     sum(t.amount) as total_transaction_volume,
     avg(t.amount) as avg_transaction_size,
     count(DISTINCT referral) as referrals_made,
     count(DISTINCT referred) as referrals_received,
     sum(r.amount) as total_rewards_earned,
     count(DISTINCT r) as total_reward_events,
     max(t.transaction_date) as last_transaction_date,
     collect(DISTINCT rr.type) as active_rule_types

// Calculate performance scores and rankings
WITH p,
     total_transactions,
     total_transaction_volume,
     avg_transaction_size,
     referrals_made,
     referrals_received,
     total_rewards_earned,
     total_reward_events,
     last_transaction_date,
     active_rule_types,
     // Performance score calculation
     (coalesce(total_transaction_volume, 0) * 0.4 + 
      coalesce(referrals_made, 0) * 100 * 0.3 + 
      coalesce(total_transactions, 0) * 10 * 0.3) as performance_score

// Return formatted results optimized for dashboard UI rendering
RETURN 
  // Core Partner Identity
  p.id as partner_id,
  p.code as partner_code,
  p.name as partner_name,
  p.tier as current_tier,
  p.value as partner_value,
  
  // Transaction Metrics (UI-ready with formatting)
  coalesce(total_transactions, 0) as total_transactions,
  round(coalesce(total_transaction_volume, 0.0), 2) as total_volume,
  round(coalesce(avg_transaction_size, 0.0), 2) as avg_transaction_size,
  
  // Network Metrics
  coalesce(referrals_made, 0) as referrals_made,
  coalesce(referrals_received, 0) as referrals_received,
  
  // Reward Metrics with precision for financial display
  round(coalesce(total_rewards_earned, 0.0), 2) as total_rewards,
  coalesce(total_reward_events, 0) as reward_events_count,
  
  // Performance Indicators for dashboard widgets
  round(performance_score, 2) as performance_score,
  last_transaction_date,
  
  // Status Indicators with real-time context
  CASE 
    WHEN coalesce($realtime, true) AND last_transaction_date >= date_sub(date(), duration({months: 1})) THEN 'active'
    WHEN coalesce($realtime, true) AND last_transaction_date >= date_sub(date(), duration({months: 3})) THEN 'inactive' 
    WHEN last_transaction_date >= date('2024-01-01') THEN 'active'
    WHEN last_transaction_date >= date('2023-07-01') THEN 'inactive'
    ELSE 'dormant'
  END as activity_status,
  
  // Rule Information for operational dashboard
  size(active_rule_types) as active_rules_count,
  active_rule_types,
  
  // Tier-specific performance indicators
  {
    tier_rank: CASE p.tier
      WHEN 'platinum' THEN 4
      WHEN 'gold' THEN 3 
      WHEN 'silver' THEN 2
      WHEN 'bronze' THEN 1
      ELSE 0
    END,
    tier_color: CASE p.tier
      WHEN 'platinum' THEN '#E5E4E2'
      WHEN 'gold' THEN '#FFD700'
      WHEN 'silver' THEN '#C0C0C0'
      WHEN 'bronze' THEN '#CD7F32'
      ELSE '#808080'
    END,
    next_tier_threshold: CASE p.tier
      WHEN 'bronze' THEN 5000
      WHEN 'silver' THEN 15000
      WHEN 'gold' THEN 50000
      ELSE null
    END
  } as tier_info,
  
  // Real-time timestamps for dashboard refresh logic
  CASE 
    WHEN coalesce($realtime, true) THEN {
      partner_since: p.created_at,
      last_updated: p.updated_at,
      data_timestamp: timestamp(),
      refresh_interval: 300 // 5 minutes for real-time dashboards
    }
    ELSE {
      partner_since: p.created_at,
      last_updated: p.updated_at,
      data_timestamp: null,
      refresh_interval: 3600 // 1 hour for static reports
    }
  END as timestamp_info,
  
  // Dashboard metadata for UI rendering
  {
    data_quality: CASE 
      WHEN total_transactions > 10 THEN 'high'
      WHEN total_transactions > 3 THEN 'medium'
      WHEN total_transactions > 0 THEN 'low'
      ELSE 'insufficient'
    END,
    currency: 'USD',
    locale: 'en-US'
  } as ui_metadata

ORDER BY 
  // Dynamic sorting based on $sortBy parameter
  CASE 
    WHEN $sortBy = 'revenue' THEN -total_transaction_volume
    WHEN $sortBy = 'activity' THEN -total_transactions
    WHEN $sortBy = 'tier' THEN -CASE p.tier WHEN 'platinum' THEN 4 WHEN 'gold' THEN 3 WHEN 'silver' THEN 2 WHEN 'bronze' THEN 1 ELSE 0 END
    ELSE -performance_score  // Default to performance
  END,
  CASE WHEN $partnerId IS NOT NULL THEN 0 ELSE 1 END,
  performance_score DESC
  
LIMIT coalesce($topN, 10);