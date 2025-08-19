// =============================================================================
// Query: Compare Product Profitability
// Purpose: Product and plan profitability analysis for strategic planning
// Pain Point: "Which products should we focus our partners on to maximize profitability?"
// =============================================================================
//
// Parameters:
// $startDate: Analysis start date (format: 'YYYY-MM-DD')
// $endDate: Analysis end date (format: 'YYYY-MM-DD')
// $productTypes: Array of product types to analyze (optional, analyzes all if null)
// $partnerTierFilter: Focus on specific partner tier ('bronze', 'silver', 'gold', 'platinum')
// $includeMarginAnalysis: Include detailed margin analysis (true/false)
// $minTransactionCount: Minimum transactions required for inclusion in analysis
//
// Business Metrics Provided:
// - Product-level revenue and profitability analysis
// - Partner performance by product type
// - Cross-sell and upsell opportunity identification
// - Product portfolio optimization recommendations
// - Reward cost efficiency by product category

// Note: This query assumes transaction types represent different products/plans
// In a real implementation, you might have separate Product nodes

MATCH (t:Transaction)-[:TRIGGERED_BY]-(r:Reward)
MATCH (p:Partner)-[:APPLIES_RULE]-(rule:RewardRule)
WHERE t.partner_id = p.id
  AND t.transaction_date >= date($startDate) 
  AND t.transaction_date <= date($endDate)
  AND t.status = 'confirmed'
  AND ($productTypes IS NULL OR t.type IN $productTypes)
  AND ($partnerTierFilter IS NULL OR p.tier = $partnerTierFilter)

// Aggregate by product type (transaction type) and partner tier
WITH t.type AS product_type,
  p.tier AS partner_tier,
  rule.type AS reward_structure,
  count(t.id) AS transaction_count,
  count(DISTINCT p.id) AS unique_partners,
  sum(t.amount) AS total_revenue,
  sum(r.amount) AS total_rewards,
  avg(t.amount) AS avg_transaction_value,
  avg(r.amount) AS avg_reward_cost,
  max(t.transaction_date) AS latest_transaction,
  min(t.transaction_date) AS earliest_transaction

// Filter by minimum transaction count if specified
WHERE ($minTransactionCount IS NULL OR transaction_count >= $minTransactionCount)

// Calculate profitability metrics
WITH product_type, partner_tier, reward_structure,
  transaction_count, unique_partners, total_revenue, total_rewards,
  avg_transaction_value, avg_reward_cost, latest_transaction, earliest_transaction,
  (total_revenue - total_rewards) AS net_contribution,
  CASE WHEN total_revenue > 0 THEN (total_rewards / total_revenue) * 100 ELSE 0 END AS reward_rate_percent,
  CASE WHEN unique_partners > 0 THEN total_revenue / unique_partners ELSE 0 END AS revenue_per_partner,
  CASE WHEN unique_partners > 0 THEN transaction_count / unique_partners ELSE 0 END AS transactions_per_partner

// Calculate market share and penetration
WITH product_type, partner_tier, reward_structure, transaction_count, unique_partners,
  total_revenue, total_rewards, avg_transaction_value, avg_reward_cost,
  latest_transaction, earliest_transaction, net_contribution, reward_rate_percent,
  revenue_per_partner, transactions_per_partner

// Get partner adoption patterns by product
OPTIONAL MATCH (adoption_p:Partner)
WHERE ($partnerTierFilter IS NULL OR adoption_p.tier = $partnerTierFilter)
OPTIONAL MATCH (adoption_t:Transaction)
WHERE adoption_t.partner_id = adoption_p.id
  AND adoption_t.type = product_type
  AND adoption_t.transaction_date >= date($startDate) 
  AND adoption_t.transaction_date <= date($endDate)
  AND adoption_t.status = 'confirmed'

WITH product_type, partner_tier, reward_structure, transaction_count, unique_partners,
  total_revenue, total_rewards, avg_transaction_value, avg_reward_cost,
  latest_transaction, earliest_transaction, net_contribution, reward_rate_percent,
  revenue_per_partner, transactions_per_partner,
  count(DISTINCT adoption_p.id) AS total_tier_partners,
  CASE 
    WHEN count(DISTINCT adoption_p.id) > 0 
    THEN (unique_partners * 100.0) / count(DISTINCT adoption_p.id)
    ELSE 0 
  END AS adoption_rate_percent

// Calculate time-based performance trends
OPTIONAL MATCH (trend_t:Transaction)-[:TRIGGERED_BY]-(trend_r:Reward)
WHERE trend_t.type = product_type
  AND trend_t.transaction_date >= date($startDate) 
  AND trend_t.transaction_date <= date($endDate)
  AND trend_t.status = 'confirmed'
  AND ($partnerTierFilter IS NULL OR EXISTS {
    MATCH (trend_p:Partner) 
    WHERE trend_t.partner_id = trend_p.id AND trend_p.tier = $partnerTierFilter
  })

WITH product_type, partner_tier, reward_structure, transaction_count, unique_partners,
  total_revenue, total_rewards, avg_transaction_value, avg_reward_cost,
  latest_transaction, earliest_transaction, net_contribution, reward_rate_percent,
  revenue_per_partner, transactions_per_partner, total_tier_partners, adoption_rate_percent,
  
  // Monthly trend data
  trend_t.transaction_date.year AS trend_year,
  trend_t.transaction_date.month AS trend_month,
  sum(trend_t.amount) AS monthly_revenue,
  sum(trend_r.amount) AS monthly_rewards,
  count(trend_t.id) AS monthly_transactions

WITH product_type, partner_tier, reward_structure, transaction_count, unique_partners,
  total_revenue, total_rewards, avg_transaction_value, avg_reward_cost,
  latest_transaction, earliest_transaction, net_contribution, reward_rate_percent,
  revenue_per_partner, transactions_per_partner, total_tier_partners, adoption_rate_percent,
  COLLECT({
    period: date(toString(trend_year) + '-' + 
                CASE WHEN trend_month < 10 THEN '0' + toString(trend_month) ELSE toString(trend_month) END + '-01'),
    revenue: COALESCE(monthly_revenue, 0),
    rewards: COALESCE(monthly_rewards, 0),
    transactions: COALESCE(monthly_transactions, 0),
    net_contribution: COALESCE(monthly_revenue, 0) - COALESCE(monthly_rewards, 0)
  }) AS monthly_trends

// Calculate growth and volatility metrics
WITH product_type, partner_tier, reward_structure, transaction_count, unique_partners,
  total_revenue, total_rewards, avg_transaction_value, avg_reward_cost,
  latest_transaction, earliest_transaction, net_contribution, reward_rate_percent,
  revenue_per_partner, transactions_per_partner, total_tier_partners, adoption_rate_percent,
  monthly_trends,
  
  // Growth calculation
  CASE 
    WHEN size(monthly_trends) >= 3 AND monthly_trends[0].revenue > 0
    THEN ((monthly_trends[-1].revenue - monthly_trends[0].revenue) / monthly_trends[0].revenue) * 100
    ELSE NULL 
  END AS revenue_growth_percent,
  
  // Average monthly performance
  CASE 
    WHEN size(monthly_trends) > 0
    THEN reduce(sum = 0, item IN monthly_trends | sum + item.revenue) / size(monthly_trends)
    ELSE 0
  END AS avg_monthly_revenue

// Aggregate product-level data
WITH COLLECT({
  product_type: product_type,
  partner_tier: partner_tier,
  reward_structure: reward_structure,
  performance: {
    transaction_count: transaction_count,
    unique_partners: unique_partners,
    total_revenue: total_revenue,
    total_rewards: total_rewards,
    net_contribution: net_contribution,
    reward_rate_percent: reward_rate_percent,
    avg_transaction_value: avg_transaction_value,
    avg_reward_cost: avg_reward_cost,
    revenue_per_partner: revenue_per_partner,
    transactions_per_partner: transactions_per_partner
  },
  adoption: {
    total_tier_partners: total_tier_partners,
    adoption_rate_percent: adoption_rate_percent,
    latest_transaction: latest_transaction,
    earliest_transaction: earliest_transaction
  },
  trends: {
    monthly_data: monthly_trends,
    revenue_growth_percent: revenue_growth_percent,
    avg_monthly_revenue: avg_monthly_revenue,
    volatility_score: CASE 
      WHEN size(monthly_trends) > 1 AND avg_monthly_revenue > 0
      THEN sqrt(reduce(variance = 0, item IN monthly_trends | 
                      variance + (item.revenue - avg_monthly_revenue) * (item.revenue - avg_monthly_revenue)
                     ) / size(monthly_trends)) / avg_monthly_revenue * 100
      ELSE 0
    END
  }
}) AS product_tier_data

// Aggregate by product across all tiers
UNWIND product_tier_data AS ptd
WITH ptd.product_type AS product,
  sum(ptd.performance.total_revenue) AS product_total_revenue,
  sum(ptd.performance.total_rewards) AS product_total_rewards,
  sum(ptd.performance.transaction_count) AS product_total_transactions,
  sum(ptd.performance.unique_partners) AS product_total_partners,
  avg(ptd.performance.avg_transaction_value) AS product_avg_transaction_value,
  avg(ptd.adoption.adoption_rate_percent) AS product_avg_adoption_rate,
  avg(ptd.trends.revenue_growth_percent) AS product_avg_growth_rate,
  avg(ptd.trends.volatility_score) AS product_avg_volatility,
  product_tier_data

WITH product,
  product_total_revenue,
  product_total_rewards,
  (product_total_revenue - product_total_rewards) AS product_net_contribution,
  CASE WHEN product_total_revenue > 0 THEN (product_total_rewards / product_total_revenue) * 100 ELSE 0 END AS product_reward_rate,
  product_total_transactions,
  product_total_partners,
  product_avg_transaction_value,
  product_avg_adoption_rate,
  product_avg_growth_rate,
  product_avg_volatility,
  [ptd IN product_tier_data WHERE ptd.product_type = product] AS tier_breakdown,
  product_tier_data

// Calculate overall system metrics for comparison
WITH COLLECT({
  product_name: product,
  metrics: {
    total_revenue: product_total_revenue,
    total_rewards: product_total_rewards,
    net_contribution: product_net_contribution,
    reward_rate_percent: product_reward_rate,
    total_transactions: product_total_transactions,
    total_partners: product_total_partners,
    avg_transaction_value: product_avg_transaction_value,
    avg_adoption_rate: product_avg_adoption_rate,
    growth_rate_percent: product_avg_growth_rate,
    volatility_score: product_avg_volatility
  },
  tier_analysis: tier_breakdown
}) AS all_products_data,
  reduce(system_revenue = 0, item IN product_tier_data | system_revenue + item.performance.total_revenue) AS system_total_revenue,
  reduce(system_rewards = 0, item IN product_tier_data | system_rewards + item.performance.total_rewards) AS system_total_rewards

// Calculate product rankings and market share
UNWIND all_products_data AS product_data
WITH all_products_data, product_data, system_total_revenue, system_total_rewards,
  (product_data.metrics.total_revenue / system_total_revenue) * 100 AS revenue_market_share,
  (product_data.metrics.total_rewards / system_total_rewards) * 100 AS reward_cost_share

WITH all_products_data, system_total_revenue, system_total_rewards,
  COLLECT({
    product: product_data,
    market_position: {
      revenue_market_share: revenue_market_share,
      reward_cost_share: reward_cost_share,
      revenue_rank: apoc.coll.indexOf(
        [item IN all_products_data ORDER BY item.metrics.total_revenue DESC], 
        product_data
      ) + 1,
      profitability_rank: apoc.coll.indexOf(
        [item IN all_products_data ORDER BY item.metrics.net_contribution DESC], 
        product_data
      ) + 1,
      efficiency_rank: apoc.coll.indexOf(
        [item IN all_products_data ORDER BY item.metrics.reward_rate_percent ASC], 
        product_data
      ) + 1,
      growth_rank: apoc.coll.indexOf(
        [item IN all_products_data ORDER BY item.metrics.growth_rate_percent DESC], 
        product_data
      ) + 1
    }
  }) AS ranked_products

// Generate margin analysis if requested
WITH ranked_products, system_total_revenue, system_total_rewards,
  CASE 
    WHEN $includeMarginAnalysis = true 
    THEN [product_analysis IN ranked_products | {
      product_name: product_analysis.product.product_name,
      margin_metrics: {
        gross_margin_percent: CASE 
          WHEN product_analysis.product.metrics.total_revenue > 0
          THEN ((product_analysis.product.metrics.total_revenue - product_analysis.product.metrics.total_rewards) / product_analysis.product.metrics.total_revenue) * 100
          ELSE 0
        END,
        reward_efficiency: CASE 
          WHEN product_analysis.product.metrics.total_rewards > 0
          THEN product_analysis.product.metrics.net_contribution / product_analysis.product.metrics.total_rewards
          ELSE 0
        END,
        partner_productivity: CASE 
          WHEN product_analysis.product.metrics.total_partners > 0
          THEN product_analysis.product.metrics.total_revenue / product_analysis.product.metrics.total_partners
          ELSE 0
        END,
        transaction_efficiency: CASE 
          WHEN product_analysis.product.metrics.total_transactions > 0
          THEN product_analysis.product.metrics.net_contribution / product_analysis.product.metrics.total_transactions
          ELSE 0
        END
      }
    }]
    ELSE NULL 
  END AS margin_analysis

RETURN {
  analysis_metadata: {
    period: $startDate + ' to ' + $endDate,
    products_analyzed: size(ranked_products),
    partner_tier_filter: $partnerTierFilter,
    min_transaction_threshold: $minTransactionCount,
    system_totals: {
      total_revenue: system_total_revenue,
      total_rewards: system_total_rewards,
      system_net_contribution: system_total_revenue - system_total_rewards,
      system_reward_rate: (system_total_rewards / system_total_revenue) * 100
    }
  },
  product_comparison: [product_analysis IN ranked_products | {
    product: product_analysis.product.product_name,
    performance_metrics: product_analysis.product.metrics,
    market_position: product_analysis.market_position,
    profitability_score: (
      (100 - product_analysis.market_position.profitability_rank * 5) +
      (100 - product_analysis.market_position.efficiency_rank * 5) +
      (product_analysis.market_position.revenue_market_share * 2) +
      CASE 
        WHEN product_analysis.product.metrics.growth_rate_percent > 0 
        THEN product_analysis.product.metrics.growth_rate_percent 
        ELSE 0 
      END
    ) / 4,
    tier_breakdown: product_analysis.product.tier_analysis,
    strategic_category: CASE 
      WHEN product_analysis.market_position.revenue_rank <= 2 AND product_analysis.product.metrics.growth_rate_percent > 10
      THEN 'star_product'
      WHEN product_analysis.market_position.revenue_rank <= 3 AND product_analysis.product.metrics.growth_rate_percent <= 0
      THEN 'cash_cow'
      WHEN product_analysis.market_position.revenue_rank > 3 AND product_analysis.product.metrics.growth_rate_percent > 5
      THEN 'rising_star'
      WHEN product_analysis.market_position.profitability_rank > size(ranked_products) * 0.7
      THEN 'question_mark'
      ELSE 'stable_performer'
    END
  }],
  insights: {
    most_profitable_product: ranked_products[0].product.product_name,
    most_efficient_product: [p IN ranked_products WHERE p.market_position.efficiency_rank = 1][0].product.product_name,
    fastest_growing_product: [p IN ranked_products WHERE p.market_position.growth_rank = 1][0].product.product_name,
    highest_adoption_product: [p IN ranked_products ORDER BY p.product.metrics.avg_adoption_rate DESC][0].product.product_name,
    underperforming_products: [p IN ranked_products 
                              WHERE p.product.metrics.reward_rate_percent > 20 
                              OR p.product.metrics.growth_rate_percent < -5],
    portfolio_concentration: CASE 
      WHEN size([p IN ranked_products WHERE p.market_position.revenue_market_share > 40]) > 0
      THEN 'high_concentration'
      WHEN size([p IN ranked_products WHERE p.market_position.revenue_market_share > 25]) <= 2
      THEN 'moderate_concentration'
      ELSE 'diversified'
    END,
    cross_sell_opportunities: [p IN ranked_products 
                              WHERE p.product.metrics.avg_adoption_rate < 30 
                              AND p.product.metrics.growth_rate_percent > 0][0..3]
  },
  margin_analysis: margin_analysis,
  strategic_recommendations: {
    product_focus_priorities: [
      CASE 
        WHEN size([p IN ranked_products WHERE p.market_position.profitability_rank = 1 AND p.product.metrics.growth_rate_percent > 0]) > 0
        THEN 'double_down_on_top_performers'
        ELSE NULL 
      END,
      CASE 
        WHEN size([p IN ranked_products WHERE p.product.metrics.reward_rate_percent > 25]) > 0
        THEN 'optimize_high_cost_products'
        ELSE NULL 
      END,
      CASE 
        WHEN size([p IN ranked_products WHERE p.product.metrics.avg_adoption_rate < 20]) > 0
        THEN 'improve_product_adoption'
        ELSE NULL 
      END
    ],
    portfolio_actions: CASE 
      WHEN size(ranked_products) > 5 
      THEN ['consider_product_consolidation', 'focus_resources_on_winners']
      WHEN size([p IN ranked_products WHERE p.market_position.revenue_market_share > 50]) > 0
      THEN ['diversify_product_portfolio', 'reduce_concentration_risk']
      ELSE ['optimize_existing_portfolio', 'test_new_products']
    END,
    partner_enablement: [
      CASE 
        WHEN size([p IN ranked_products WHERE p.product.metrics.avg_adoption_rate < 40]) > 0
        THEN 'improve_partner_product_training'
        ELSE NULL 
      END,
      CASE 
        WHEN avg([p IN ranked_products | p.product.metrics.volatility_score]) > 30
        THEN 'stabilize_partner_product_performance'
        ELSE NULL 
      END
    ],
    reward_optimization: [p IN ranked_products 
                         WHERE p.product.metrics.reward_rate_percent > 
                               avg([item IN ranked_products | item.product.metrics.reward_rate_percent]) * 1.5]
  }
} AS product_profitability_analysis