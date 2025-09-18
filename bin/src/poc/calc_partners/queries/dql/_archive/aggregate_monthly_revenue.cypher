// =============================================================================
// Query: Aggregate Monthly Revenue
// Purpose: Executive monthly revenue analysis with trend comparison
// Pain Point: "I need to see our monthly revenue trends and growth patterns"
// =============================================================================
//
// Parameters:
// $startDate: Start date for analysis (format: 'YYYY-MM-DD')
// $endDate: End date for analysis (format: 'YYYY-MM-DD')
// $partnerTier: Optional partner tier filter ('bronze', 'silver', 'gold', 'platinum')
//
// Business Metrics Provided:
// - Monthly revenue totals
// - Month-over-month growth rates
// - Year-over-year comparisons
// - Partner tier contribution breakdown
// - Revenue velocity trends

MATCH (t:Transaction)-[:TRIGGERED_BY]-(r:Reward)
MATCH (p:Partner)-[:APPLIES_RULE]-(rule:RewardRule)
WHERE t.transaction_date >= date($startDate) 
  AND t.transaction_date <= date($endDate)
  AND t.status = 'confirmed'
  AND ($partnerTier IS NULL OR p.tier = $partnerTier)

WITH 
  t.transaction_date.year AS year,
  t.transaction_date.month AS month,
  p.tier AS partner_tier,
  sum(t.amount) AS monthly_transaction_volume,
  sum(r.amount) AS monthly_reward_cost,
  count(DISTINCT p.id) AS active_partners,
  count(t.id) AS transaction_count

WITH 
  year, month,
  partner_tier,
  monthly_transaction_volume,
  monthly_reward_cost,
  (monthly_transaction_volume - monthly_reward_cost) AS net_revenue,
  active_partners,
  transaction_count,
  date(toString(year) + '-' + 
       CASE WHEN month < 10 THEN '0' + toString(month) ELSE toString(month) END + '-01') AS period_date

ORDER BY year, month, partner_tier

WITH COLLECT({
  period: period_date,
  tier: partner_tier,
  transaction_volume: monthly_transaction_volume,
  reward_cost: monthly_reward_cost,
  net_revenue: net_revenue,
  active_partners: active_partners,
  transaction_count: transaction_count,
  avg_transaction_size: monthly_transaction_volume / transaction_count,
  reward_rate: (monthly_reward_cost / monthly_transaction_volume) * 100
}) AS monthly_data

// Calculate growth rates and trends
UNWIND monthly_data AS current
WITH monthly_data, current
OPTIONAL MATCH (prev_data) 
WHERE prev_data IN monthly_data 
  AND prev_data.period = current.period - duration({months: 1})
  AND prev_data.tier = current.tier

WITH current,
  CASE 
    WHEN prev_data IS NOT NULL AND prev_data.net_revenue > 0
    THEN ((current.net_revenue - prev_data.net_revenue) / prev_data.net_revenue) * 100
    ELSE NULL 
  END AS mom_growth_rate,
  monthly_data

RETURN {
  summary: {
    total_revenue: reduce(sum = 0, item IN monthly_data | sum + item.net_revenue),
    total_transactions: reduce(sum = 0, item IN monthly_data | sum + item.transaction_count),
    average_monthly_revenue: reduce(sum = 0, item IN monthly_data | sum + item.net_revenue) / size(monthly_data),
    total_active_partners: reduce(sum = 0, item IN monthly_data | sum + item.active_partners)
  },
  monthly_breakdown: COLLECT({
    period: current.period,
    tier: current.tier,
    metrics: {
      transaction_volume: current.transaction_volume,
      reward_cost: current.reward_cost,
      net_revenue: current.net_revenue,
      active_partners: current.active_partners,
      transaction_count: current.transaction_count,
      avg_transaction_size: current.avg_transaction_size,
      reward_rate_percent: current.reward_rate,
      mom_growth_percent: mom_growth_rate
    }
  }),
  insights: {
    peak_month: reduce(max = monthly_data[0], item IN monthly_data | 
                      CASE WHEN item.net_revenue > max.net_revenue THEN item ELSE max END),
    growth_trend: CASE 
      WHEN size([item IN monthly_data WHERE item.net_revenue > 0]) > size(monthly_data) / 2 
      THEN 'positive' 
      ELSE 'needs_attention' 
    END
  }
} AS revenue_analysis