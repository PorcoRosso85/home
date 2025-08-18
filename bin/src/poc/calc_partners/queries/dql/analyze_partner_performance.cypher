// =============================================================================
// Query: Analyze Partner Performance
// Purpose: Deep dive performance analysis with predictive insights
// Pain Point: "I need to understand partner behavior patterns and predict future performance"
// =============================================================================
//
// Parameters:
// $partnerId: Specific partner ID for analysis (optional)
// $startDate: Analysis start date (format: 'YYYY-MM-DD')
// $endDate: Analysis end date (format: 'YYYY-MM-DD')
// $benchmarkTier: Tier to use for benchmarking ('bronze', 'silver', 'gold', 'platinum')
// $includeProjections: Whether to include performance projections (true/false)
//
// Business Metrics Provided:
// - Performance trends and seasonality
// - Benchmark comparisons against tier averages
// - Behavioral pattern analysis
// - Risk assessment and early warning indicators
// - Performance projections and recommendations

MATCH (p:Partner)
WHERE ($partnerId IS NULL OR p.id = $partnerId)

// Get partner's transaction history
OPTIONAL MATCH (p)-[:APPLIES_RULE]-(rule:RewardRule)
OPTIONAL MATCH (t:Transaction)-[:TRIGGERED_BY]-(r:Reward)
WHERE t.partner_id = p.id
  AND t.transaction_date >= date($startDate) 
  AND t.transaction_date <= date($endDate)
  AND t.status = 'confirmed'

// Get referral network
OPTIONAL MATCH (p)-[ref:REFERS*1..2]-(referred:Partner)
OPTIONAL MATCH (rt:Transaction)-[:TRIGGERED_BY]-(rr:Reward)
WHERE rt.partner_id = referred.id
  AND rt.transaction_date >= date($startDate) 
  AND rt.transaction_date <= date($endDate)
  AND rt.status = 'confirmed'

// Aggregate monthly performance data
WITH p, rule,
  t.transaction_date.year AS year,
  t.transaction_date.month AS month,
  count(t.id) AS monthly_transactions,
  sum(t.amount) AS monthly_revenue,
  sum(r.amount) AS monthly_rewards,
  avg(t.amount) AS monthly_avg_transaction,
  count(DISTINCT referred.id) AS monthly_referrals,
  sum(rt.amount) AS monthly_referral_revenue

WITH p, rule,
  year, month,
  monthly_transactions,
  monthly_revenue,
  monthly_rewards,
  monthly_avg_transaction,
  monthly_referrals,
  monthly_referral_revenue,
  date(toString(year) + '-' + 
       CASE WHEN month < 10 THEN '0' + toString(month) ELSE toString(month) END + '-01') AS period

// Collect monthly data for trend analysis
WITH p, rule,
  COLLECT({
    period: period,
    transactions: COALESCE(monthly_transactions, 0),
    revenue: COALESCE(monthly_revenue, 0),
    rewards: COALESCE(monthly_rewards, 0),
    avg_transaction: COALESCE(monthly_avg_transaction, 0),
    referrals: COALESCE(monthly_referrals, 0),
    referral_revenue: COALESCE(monthly_referral_revenue, 0),
    net_contribution: COALESCE(monthly_revenue, 0) - COALESCE(monthly_rewards, 0)
  }) AS monthly_performance
  ORDER BY period

// Calculate overall partner metrics
WITH p, rule, monthly_performance,
  reduce(sum = 0, item IN monthly_performance | sum + item.revenue) AS total_revenue,
  reduce(sum = 0, item IN monthly_performance | sum + item.rewards) AS total_rewards,
  reduce(sum = 0, item IN monthly_performance | sum + item.transactions) AS total_transactions,
  reduce(sum = 0, item IN monthly_performance | sum + item.referrals) AS total_referrals,
  size(monthly_performance) AS active_months

// Get benchmark data for comparison
OPTIONAL MATCH (benchmark_p:Partner)
WHERE benchmark_p.tier = COALESCE($benchmarkTier, p.tier)
OPTIONAL MATCH (bt:Transaction)-[:TRIGGERED_BY]-(br:Reward)
WHERE bt.partner_id = benchmark_p.id
  AND bt.transaction_date >= date($startDate) 
  AND bt.transaction_date <= date($endDate)
  AND bt.status = 'confirmed'

WITH p, rule, monthly_performance, total_revenue, total_rewards, total_transactions, total_referrals, active_months,
  avg(bt.amount) AS benchmark_avg_transaction,
  avg(count(bt.id)) AS benchmark_avg_monthly_transactions,
  avg(sum(bt.amount)) AS benchmark_avg_monthly_revenue

// Calculate performance indicators
WITH p, rule, monthly_performance, total_revenue, total_rewards, total_transactions, total_referrals, active_months,
  benchmark_avg_transaction, benchmark_avg_monthly_transactions, benchmark_avg_monthly_revenue,
  
  // Trend analysis
  CASE 
    WHEN size(monthly_performance) >= 3
    THEN (monthly_performance[-1].revenue - monthly_performance[0].revenue) / 
         CASE WHEN monthly_performance[0].revenue > 0 THEN monthly_performance[0].revenue ELSE 1 END * 100
    ELSE NULL 
  END AS revenue_trend_percent,
  
  // Consistency score (lower coefficient of variation = more consistent)
  CASE 
    WHEN size(monthly_performance) >= 3 AND reduce(sum = 0, item IN monthly_performance | sum + item.revenue) > 0
    THEN reduce(avg = 0, item IN monthly_performance | avg + item.revenue) / size(monthly_performance)
    ELSE 0
  END AS avg_monthly_revenue,
  
  // Recency and activity patterns
  CASE 
    WHEN size(monthly_performance) > 0 
    THEN duration.between(monthly_performance[-1].period, date()).days
    ELSE 999 
  END AS days_since_last_activity,
  
  // Performance versus benchmark
  CASE 
    WHEN benchmark_avg_monthly_revenue > 0 AND active_months > 0
    THEN ((total_revenue / active_months) / benchmark_avg_monthly_revenue) * 100
    ELSE NULL 
  END AS benchmark_performance_percent

// Calculate volatility and consistency
WITH p, rule, monthly_performance, total_revenue, total_rewards, total_transactions, total_referrals,
  active_months, benchmark_avg_transaction, benchmark_avg_monthly_transactions, benchmark_avg_monthly_revenue,
  revenue_trend_percent, avg_monthly_revenue, days_since_last_activity, benchmark_performance_percent,
  
  // Calculate standard deviation for volatility
  reduce(variance = 0, item IN monthly_performance | 
    variance + (item.revenue - avg_monthly_revenue) * (item.revenue - avg_monthly_revenue)
  ) / size(monthly_performance) AS revenue_variance

WITH p, rule, monthly_performance, total_revenue, total_rewards, total_transactions, total_referrals,
  active_months, benchmark_avg_transaction, benchmark_avg_monthly_transactions, benchmark_avg_monthly_revenue,
  revenue_trend_percent, avg_monthly_revenue, days_since_last_activity, benchmark_performance_percent,
  sqrt(revenue_variance) AS revenue_std_dev,
  
  // Risk indicators
  size([item IN monthly_performance WHERE item.revenue = 0]) AS zero_revenue_months,
  size([item IN monthly_performance WHERE item.transactions <= 1]) AS low_activity_months

// Generate projections if requested
WITH p, rule, monthly_performance, total_revenue, total_rewards, total_transactions, total_referrals,
  active_months, benchmark_avg_transaction, benchmark_avg_monthly_transactions, benchmark_avg_monthly_revenue,
  revenue_trend_percent, avg_monthly_revenue, days_since_last_activity, benchmark_performance_percent,
  revenue_std_dev, zero_revenue_months, low_activity_months,
  
  CASE WHEN $includeProjections = true AND revenue_trend_percent IS NOT NULL
    THEN avg_monthly_revenue * (1 + (revenue_trend_percent / 100)) * 3  // 3-month projection
    ELSE NULL 
  END AS projected_quarterly_revenue,
  
  // Performance scoring
  CASE 
    WHEN benchmark_performance_percent IS NOT NULL
    THEN CASE 
      WHEN benchmark_performance_percent >= 120 THEN 'excellent'
      WHEN benchmark_performance_percent >= 100 THEN 'above_average'
      WHEN benchmark_performance_percent >= 80 THEN 'average'
      WHEN benchmark_performance_percent >= 60 THEN 'below_average'
      ELSE 'poor'
    END
    ELSE 'no_benchmark'
  END AS performance_rating

RETURN {
  partner: {
    id: p.id,
    code: p.code,
    name: p.name,
    tier: p.tier,
    rule_type: rule.type
  },
  analysis_period: {
    start_date: $startDate,
    end_date: $endDate,
    active_months: active_months,
    benchmark_tier: COALESCE($benchmarkTier, p.tier)
  },
  performance_summary: {
    total_revenue: total_revenue,
    total_rewards: total_rewards,
    net_contribution: total_revenue - total_rewards,
    total_transactions: total_transactions,
    total_referrals: total_referrals,
    avg_monthly_revenue: avg_monthly_revenue,
    avg_transaction_size: CASE WHEN total_transactions > 0 THEN total_revenue / total_transactions ELSE 0 END,
    reward_efficiency: CASE WHEN total_revenue > 0 THEN (total_rewards / total_revenue) * 100 ELSE 0 END
  },
  trend_analysis: {
    revenue_trend_percent: revenue_trend_percent,
    volatility_score: CASE 
      WHEN avg_monthly_revenue > 0 THEN (revenue_std_dev / avg_monthly_revenue) * 100 
      ELSE 0 
    END,
    consistency_rating: CASE 
      WHEN zero_revenue_months = 0 AND low_activity_months <= active_months * 0.2 THEN 'highly_consistent'
      WHEN zero_revenue_months <= active_months * 0.1 THEN 'consistent'
      WHEN zero_revenue_months <= active_months * 0.3 THEN 'moderate'
      ELSE 'inconsistent'
    END,
    seasonality_detected: size(monthly_performance) >= 12 AND 
      abs(reduce(sum = 0, item IN monthly_performance[0..5] | sum + item.revenue) - 
          reduce(sum = 0, item IN monthly_performance[6..11] | sum + item.revenue)) > avg_monthly_revenue * 2
  },
  benchmark_comparison: {
    performance_vs_tier: benchmark_performance_percent,
    performance_rating: performance_rating,
    above_benchmark_transactions: CASE 
      WHEN benchmark_avg_monthly_transactions > 0 
      THEN (total_transactions / active_months) > benchmark_avg_monthly_transactions
      ELSE NULL 
    END,
    above_benchmark_value: CASE 
      WHEN benchmark_avg_transaction > 0 AND total_transactions > 0
      THEN (total_revenue / total_transactions) > benchmark_avg_transaction
      ELSE NULL 
    END
  },
  risk_assessment: {
    recency_risk: CASE 
      WHEN days_since_last_activity > 90 THEN 'high'
      WHEN days_since_last_activity > 30 THEN 'medium'
      ELSE 'low'
    END,
    activity_risk: CASE 
      WHEN low_activity_months > active_months * 0.5 THEN 'high'
      WHEN low_activity_months > active_months * 0.3 THEN 'medium'
      ELSE 'low'
    END,
    revenue_risk: CASE 
      WHEN zero_revenue_months > active_months * 0.3 THEN 'high'
      WHEN zero_revenue_months > active_months * 0.1 THEN 'medium'
      ELSE 'low'
    END,
    days_since_last_activity: days_since_last_activity
  },
  projections: CASE 
    WHEN $includeProjections = true 
    THEN {
      quarterly_revenue_projection: projected_quarterly_revenue,
      confidence_level: CASE 
        WHEN revenue_std_dev / avg_monthly_revenue < 0.3 THEN 'high'
        WHEN revenue_std_dev / avg_monthly_revenue < 0.6 THEN 'medium'
        ELSE 'low'
      END,
      growth_trajectory: CASE 
        WHEN revenue_trend_percent > 10 THEN 'accelerating'
        WHEN revenue_trend_percent > 0 THEN 'growing'
        WHEN revenue_trend_percent > -10 THEN 'stable'
        ELSE 'declining'
      END
    }
    ELSE NULL 
  END,
  monthly_breakdown: monthly_performance,
  recommendations: {
    immediate_actions: CASE 
      WHEN days_since_last_activity > 60 THEN ['reengage_partner']
      WHEN performance_rating = 'poor' THEN ['performance_review', 'support_intervention']
      WHEN performance_rating = 'excellent' THEN ['tier_upgrade_consideration']
      ELSE ['monitor_trends']
    END,
    optimization_opportunities: CASE 
      WHEN total_referrals = 0 THEN ['referral_program_activation']
      WHEN revenue_std_dev / avg_monthly_revenue > 0.5 THEN ['consistency_improvement']
      ELSE ['maintain_current_strategy']
    END
  }
} AS partner_performance_analysis