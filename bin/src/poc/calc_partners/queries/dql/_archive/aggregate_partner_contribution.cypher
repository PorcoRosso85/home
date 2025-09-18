// =============================================================================
// Query: Aggregate Partner Contribution
// Purpose: Analyze individual partner contributions and performance metrics
// Pain Point: "Which partners are our top performers and how do they compare?"
// =============================================================================
//
// Parameters:
// $startDate: Start date for analysis (format: 'YYYY-MM-DD')
// $endDate: End date for analysis (format: 'YYYY-MM-DD')
// $minRevenue: Minimum revenue threshold for inclusion (optional)
// $topN: Number of top partners to return (default: 10)
//
// Business Metrics Provided:
// - Partner revenue contribution ranking
// - Transaction volume and frequency analysis
// - Reward efficiency metrics
// - Partner tier performance comparison
// - Network effect analysis (referral impact)

MATCH (p:Partner)
OPTIONAL MATCH (p)-[:APPLIES_RULE]-(rule:RewardRule)
OPTIONAL MATCH (t:Transaction)-[:TRIGGERED_BY]-(r:Reward)
WHERE t.partner_id = p.id
  AND t.transaction_date >= date($startDate) 
  AND t.transaction_date <= date($endDate)
  AND t.status = 'confirmed'
  AND ($minRevenue IS NULL OR t.amount >= $minRevenue)

// Calculate direct partner metrics
WITH p, rule,
  count(t.id) AS transaction_count,
  sum(t.amount) AS total_revenue,
  sum(r.amount) AS total_rewards,
  avg(t.amount) AS avg_transaction_size,
  max(t.transaction_date) AS last_transaction_date,
  min(t.transaction_date) AS first_transaction_date

// Calculate referral network impact
OPTIONAL MATCH (p)-[ref:REFERS*1..3]-(referred:Partner)
OPTIONAL MATCH (rt:Transaction)-[:TRIGGERED_BY]-(rr:Reward)
WHERE rt.partner_id = referred.id
  AND rt.transaction_date >= date($startDate) 
  AND rt.transaction_date <= date($endDate)
  AND rt.status = 'confirmed'

WITH p, rule, transaction_count, total_revenue, total_rewards, 
     avg_transaction_size, last_transaction_date, first_transaction_date,
     count(DISTINCT referred.id) AS referred_partners,
     sum(rt.amount) AS referral_revenue,
     sum(rr.amount) AS referral_rewards

// Calculate derived metrics
WITH p, rule,
  transaction_count,
  total_revenue,
  total_rewards,
  (total_revenue - total_rewards) AS net_contribution,
  CASE WHEN total_revenue > 0 THEN (total_rewards / total_revenue) * 100 ELSE 0 END AS reward_rate_percent,
  avg_transaction_size,
  CASE 
    WHEN first_transaction_date IS NOT NULL AND last_transaction_date IS NOT NULL
    THEN duration.between(first_transaction_date, last_transaction_date).days + 1
    ELSE 0 
  END AS active_days,
  referred_partners,
  COALESCE(referral_revenue, 0) AS network_revenue,
  COALESCE(referral_rewards, 0) AS network_rewards,
  last_transaction_date,
  first_transaction_date

// Calculate velocity and efficiency metrics
WITH p, rule, transaction_count, total_revenue, total_rewards, net_contribution,
     reward_rate_percent, avg_transaction_size, active_days, referred_partners,
     network_revenue, network_rewards, last_transaction_date, first_transaction_date,
     CASE WHEN active_days > 0 THEN total_revenue / active_days ELSE 0 END AS daily_revenue_velocity,
     CASE WHEN transaction_count > 0 THEN active_days / transaction_count ELSE 0 END AS avg_days_between_transactions,
     (total_revenue + network_revenue) AS total_impact_revenue,
     (total_rewards + network_rewards) AS total_impact_cost

WHERE total_revenue > 0  // Only include partners with actual revenue

// Rank partners by contribution
WITH COLLECT({
  partner: p,
  rule_type: rule.type,
  metrics: {
    transaction_count: transaction_count,
    total_revenue: total_revenue,
    total_rewards: total_rewards,
    net_contribution: net_contribution,
    reward_rate_percent: reward_rate_percent,
    avg_transaction_size: avg_transaction_size,
    daily_velocity: daily_revenue_velocity,
    avg_days_between_transactions: avg_days_between_transactions,
    active_days: active_days,
    referred_partners: referred_partners,
    network_revenue: network_revenue,
    total_impact_revenue: total_impact_revenue,
    total_impact_cost: total_impact_cost,
    network_effect_multiplier: CASE 
      WHEN total_revenue > 0 THEN total_impact_revenue / total_revenue 
      ELSE 1.0 
    END,
    last_transaction: last_transaction_date,
    first_transaction: first_transaction_date,
    recency_score: CASE 
      WHEN last_transaction_date IS NOT NULL 
      THEN 100 - (duration.between(last_transaction_date, date()).days * 2)
      ELSE 0 
    END
  }
}) AS all_partners

// Sort and limit results
UNWIND all_partners AS partner_data
WITH partner_data
ORDER BY partner_data.metrics.net_contribution DESC
LIMIT COALESCE($topN, 10)

WITH COLLECT(partner_data) AS top_partners

// Calculate summary statistics
WITH top_partners,
  reduce(sum = 0, item IN top_partners | sum + item.metrics.total_revenue) AS total_top_revenue,
  reduce(sum = 0, item IN [p IN top_partners WHERE p.partner.tier = 'platinum'] | sum + p.metrics.total_revenue) AS platinum_revenue,
  reduce(sum = 0, item IN [p IN top_partners WHERE p.partner.tier = 'gold'] | sum + p.metrics.total_revenue) AS gold_revenue,
  reduce(sum = 0, item IN [p IN top_partners WHERE p.partner.tier = 'silver'] | sum + p.metrics.total_revenue) AS silver_revenue,
  reduce(sum = 0, item IN [p IN top_partners WHERE p.partner.tier = 'bronze'] | sum + p.metrics.total_revenue) AS bronze_revenue

RETURN {
  period: {
    start_date: $startDate,
    end_date: $endDate,
    analysis_scope: "Top " + toString(size(top_partners)) + " performing partners"
  },
  summary: {
    total_analyzed_revenue: total_top_revenue,
    average_contribution: total_top_revenue / size(top_partners),
    tier_distribution: {
      platinum_revenue: platinum_revenue,
      gold_revenue: gold_revenue,
      silver_revenue: silver_revenue,
      bronze_revenue: bronze_revenue
    },
    network_effect_leaders: [p IN top_partners WHERE p.metrics.network_effect_multiplier > 1.5][0..3]
  },
  top_performers: [partner_data IN top_partners | {
    rank: apoc.coll.indexOf(top_partners, partner_data) + 1,
    partner_id: partner_data.partner.id,
    partner_code: partner_data.partner.code,
    partner_name: partner_data.partner.name,
    tier: partner_data.partner.tier,
    rule_type: partner_data.rule_type,
    performance: partner_data.metrics,
    insights: {
      performance_category: CASE 
        WHEN partner_data.metrics.recency_score > 80 AND partner_data.metrics.daily_velocity > total_top_revenue / size(top_partners) / 30
        THEN 'high_performer'
        WHEN partner_data.metrics.recency_score < 30 
        THEN 'at_risk'
        WHEN partner_data.metrics.network_effect_multiplier > 1.5
        THEN 'network_leader'
        ELSE 'stable'
      END,
      efficiency_rating: CASE 
        WHEN partner_data.metrics.reward_rate_percent < 10 THEN 'highly_efficient'
        WHEN partner_data.metrics.reward_rate_percent < 20 THEN 'efficient'
        ELSE 'needs_optimization'
      END
    }
  }],
  recommendations: {
    focus_tiers: CASE 
      WHEN platinum_revenue > (gold_revenue + silver_revenue + bronze_revenue) * 0.6
      THEN ['platinum_retention_critical']
      WHEN gold_revenue > total_top_revenue * 0.4
      THEN ['gold_tier_growth_opportunity']
      ELSE ['diversified_portfolio']
    END,
    at_risk_count: size([p IN top_partners WHERE p.metrics.recency_score < 30]),
    network_leaders_count: size([p IN top_partners WHERE p.metrics.network_effect_multiplier > 1.5])
  }
} AS partner_contribution_analysis