// =============================================================================
// Query: Get Cashflow Projection Dashboard
// Purpose: Advanced forward-looking cashflow analysis for financial planning and budgeting
// Parameters:
//   $projectionMonths (optional): Number of months to project forward (default: 12) [integer]
//   $partnerId (optional): Specific partner ID to focus projection on [string]
//   $tierFilter (optional): Filter by partner tier ('bronze', 'silver', 'gold', 'platinum') [string]
//   $baseDate (optional): Base date for projection (YYYY-MM-DD, default: current date) [string]
//   $scenarioType (optional): Projection scenario ('conservative', 'realistic', 'optimistic', default: 'realistic') [string]
//   $includeNewPartners (optional): Include projected new partner acquisitions (boolean, default: true) [boolean]
//   $confidenceLevel (optional): Confidence level for intervals ('80', '90', '95', default: '80') [string]
//   $includeSeasonality (optional): Apply seasonal adjustments (default: true) [boolean]
//   $riskProfile (optional): Risk assessment level ('low', 'medium', 'high', default: 'medium') [string]
//   $currency (optional): Currency for formatting (default: 'USD') [string]
// Returns: Monthly cashflow projections with scenario analysis, confidence intervals, and risk assessment
// Usage Example:
//   CALL { ... } WITH { projectionMonths: 18, scenarioType: "optimistic", confidenceLevel: "90" }
// =============================================================================

// Set projection parameters and enhanced calculations
WITH 
  coalesce($projectionMonths, 12) as projection_months,
  coalesce(date($baseDate), date('2024-01-01')) as base_date,
  coalesce($scenarioType, 'realistic') as scenario,
  coalesce($confidenceLevel, '80') as confidence_level,
  coalesce($includeSeasonality, true) as include_seasonality,
  coalesce($riskProfile, 'medium') as risk_profile,
  coalesce($currency, 'USD') as currency_code

// Historical performance analysis for projection baseline
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(t:Transaction)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(r:Reward)
WHERE 
  t.transaction_date >= date_sub(base_date, duration({months: 6}))
  AND t.transaction_date <= base_date
  AND t.status IN ['confirmed', 'pending']
  AND ($partnerId IS NULL OR p.id = $partnerId)
  AND ($tierFilter IS NULL OR p.tier = $tierFilter)

// Calculate historical averages and trends
WITH base_date, projection_months, scenario,
     p,
     avg(t.amount) as avg_monthly_revenue_per_partner,
     count(t) / 6.0 as avg_monthly_transactions_per_partner,
     sum(r.amount) / 6.0 as avg_monthly_rewards_per_partner,
     max(t.transaction_date) as last_activity_date

// Partner activity scoring for projection accuracy
WITH base_date, projection_months, scenario,
     p,
     coalesce(avg_monthly_revenue_per_partner, 0) as monthly_revenue,
     coalesce(avg_monthly_transactions_per_partner, 0) as monthly_transactions,
     coalesce(avg_monthly_rewards_per_partner, 0) as monthly_rewards,
     // Activity score for projection weighting
     CASE 
       WHEN last_activity_date >= date_sub(base_date, duration({months: 1})) THEN 1.0
       WHEN last_activity_date >= date_sub(base_date, duration({months: 3})) THEN 0.7
       WHEN last_activity_date >= date_sub(base_date, duration({months: 6})) THEN 0.4
       ELSE 0.1
     END as activity_multiplier,
     // Tier-based growth assumptions
     CASE p.tier
       WHEN 'platinum' THEN 1.15  // 15% growth
       WHEN 'gold' THEN 1.10      // 10% growth  
       WHEN 'silver' THEN 1.05    // 5% growth
       WHEN 'bronze' THEN 1.02    // 2% growth
       ELSE 1.0
     END as tier_growth_factor

// Scenario-based projection multipliers
WITH base_date, projection_months,
     p, monthly_revenue, monthly_transactions, monthly_rewards,
     activity_multiplier, tier_growth_factor,
     // Scenario adjustments
     CASE scenario
       WHEN 'conservative' THEN 0.8
       WHEN 'optimistic' THEN 1.3
       ELSE 1.0  // realistic
     END as scenario_multiplier

// Generate monthly projections
UNWIND range(1, projection_months) as month_offset
WITH base_date, p, month_offset,
     date_add(base_date, duration({months: month_offset})) as projection_date,
     monthly_revenue, monthly_transactions, monthly_rewards,
     activity_multiplier, tier_growth_factor, scenario_multiplier,
     // Month-based seasonality (example: higher activity in Q4)
     CASE 
       WHEN (base_date.month + month_offset - 1) % 12 + 1 IN [11, 12] THEN 1.2  // November/December boost
       WHEN (base_date.month + month_offset - 1) % 12 + 1 IN [1, 7] THEN 0.9    // January/July dip
       ELSE 1.0
     END as seasonality_factor

// Calculate projected values with compound growth
WITH projection_date,
     p,
     // Compound growth calculation
     monthly_revenue * 
     activity_multiplier * 
     scenario_multiplier * 
     seasonality_factor *
     power(tier_growth_factor, month_offset / 12.0) as projected_revenue,
     
     monthly_transactions * 
     activity_multiplier * 
     scenario_multiplier *
     power(tier_growth_factor, month_offset / 12.0) as projected_transactions,
     
     monthly_rewards * 
     activity_multiplier * 
     scenario_multiplier *
     power(tier_growth_factor, month_offset / 12.0) as projected_rewards

// Aggregate projections by month and tier
WITH projection_date,
     sum(projected_revenue) as total_projected_revenue,
     sum(projected_transactions) as total_projected_transactions,
     sum(projected_rewards) as total_projected_rewards,
     count(p) as active_partners_projected,
     // Tier breakdown
     sum(CASE WHEN p.tier = 'bronze' THEN projected_revenue ELSE 0 END) as bronze_revenue,
     sum(CASE WHEN p.tier = 'silver' THEN projected_revenue ELSE 0 END) as silver_revenue,
     sum(CASE WHEN p.tier = 'gold' THEN projected_revenue ELSE 0 END) as gold_revenue,
     sum(CASE WHEN p.tier = 'platinum' THEN projected_revenue ELSE 0 END) as platinum_revenue,
     // Cashflow components
     sum(projected_revenue) - sum(projected_rewards) as net_cashflow

// Add new partner acquisition projections (if enabled)
WITH projection_date,
     total_projected_revenue,
     total_projected_transactions,
     total_projected_rewards,
     active_partners_projected,
     bronze_revenue, silver_revenue, gold_revenue, platinum_revenue,
     net_cashflow,
     // New partner revenue (growth from acquisitions)
     CASE 
       WHEN coalesce($includeNewPartners, true) 
       THEN total_projected_revenue * 0.1  // 10% growth from new partners
       ELSE 0 
     END as new_partner_revenue

// Calculate enhanced confidence intervals and risk metrics
WITH projection_date,
     total_projected_revenue + new_partner_revenue as total_revenue,
     total_projected_transactions,
     total_projected_rewards,
     active_partners_projected,
     bronze_revenue, silver_revenue, gold_revenue, platinum_revenue,
     net_cashflow + new_partner_revenue as net_cashflow_adjusted,
     new_partner_revenue,
     
     // Enhanced confidence intervals based on confidence level parameter
     CASE confidence_level
       WHEN '90' THEN {
         lower_multiplier: 0.75,
         upper_multiplier: 1.35,
         variance_factor: 1.65  // 90% confidence
       }
       WHEN '95' THEN {
         lower_multiplier: 0.70,
         upper_multiplier: 1.45,
         variance_factor: 1.96  // 95% confidence  
       }
       ELSE {
         lower_multiplier: 0.80,
         upper_multiplier: 1.25,
         variance_factor: 1.28  // 80% confidence (default)
       }
     END as confidence_params,
     
     // Risk-adjusted projections based on risk profile
     CASE risk_profile
       WHEN 'low' THEN 0.95      // Conservative risk adjustment
       WHEN 'high' THEN 1.10     // Aggressive risk adjustment
       ELSE 1.0                  // Medium/balanced (default)
     END as risk_adjustment

// Return enhanced projection data optimized for financial dashboard display
RETURN 
  projection_date,
  
  // Enhanced formatting for dashboard display
  toString(projection_date.year) + '-' + 
  CASE 
    WHEN projection_date.month < 10 THEN '0' + toString(projection_date.month)
    ELSE toString(projection_date.month)
  END as month_label,
  
  // Core projections with risk adjustment
  round(total_revenue * risk_adjustment, 2) as projected_revenue,
  round(total_projected_transactions * risk_adjustment, 0) as projected_transactions,
  round(total_projected_rewards * risk_adjustment, 2) as projected_rewards,
  round(net_cashflow_adjusted * risk_adjustment, 2) as net_cashflow,
  active_partners_projected,
  
  // Enhanced confidence intervals based on selected confidence level
  round(total_revenue * confidence_params.lower_multiplier, 2) as revenue_low_estimate,
  round(total_revenue * confidence_params.upper_multiplier, 2) as revenue_high_estimate,
  round(net_cashflow_adjusted * confidence_params.lower_multiplier, 2) as cashflow_low_estimate,
  round(net_cashflow_adjusted * confidence_params.upper_multiplier, 2) as cashflow_high_estimate,
  
  // Tier breakdown for detailed financial analysis
  {
    bronze: round(bronze_revenue * risk_adjustment, 2),
    silver: round(silver_revenue * risk_adjustment, 2),
    gold: round(gold_revenue * risk_adjustment, 2),
    platinum: round(platinum_revenue * risk_adjustment, 2)
  } as tier_breakdown,
  
  // Revenue composition for financial planning
  {
    existing_partners: round((total_revenue - new_partner_revenue) * risk_adjustment, 2),
    new_partners: round(new_partner_revenue * risk_adjustment, 2),
    total: round(total_revenue * risk_adjustment, 2),
    growth_contribution_pct: CASE 
      WHEN total_revenue > 0 THEN round((new_partner_revenue / total_revenue) * 100, 1)
      ELSE 0.0
    END
  } as revenue_composition,
  
  // Financial ratios and metrics for executive dashboard
  {
    revenue_to_rewards_ratio: CASE 
      WHEN total_projected_rewards > 0 
      THEN round((total_revenue * risk_adjustment) / (total_projected_rewards * risk_adjustment), 2)
      ELSE null
    END,
    profit_margin_pct: CASE 
      WHEN total_revenue > 0 
      THEN round(((net_cashflow_adjusted * risk_adjustment) / (total_revenue * risk_adjustment)) * 100, 1)
      ELSE null
    END,
    cost_per_transaction: CASE 
      WHEN total_projected_transactions > 0 
      THEN round((total_projected_rewards * risk_adjustment) / (total_projected_transactions * risk_adjustment), 2)
      ELSE null
    END
  } as financial_ratios,
  
  // Enhanced projection metadata for dashboard intelligence
  {
    scenario: scenario,
    confidence_level: confidence_level + '%',
    risk_profile: risk_profile,
    base_date: base_date,
    includes_new_partners: coalesce($includeNewPartners, true),
    includes_seasonality: include_seasonality,
    currency: currency_code,
    
    projection_accuracy: CASE 
      WHEN projection_date <= date_add(base_date, duration({months: 3})) THEN 'high'
      WHEN projection_date <= date_add(base_date, duration({months: 6})) THEN 'medium'
      WHEN projection_date <= date_add(base_date, duration({months: 12})) THEN 'moderate'
      ELSE 'low'
    END,
    
    // Risk indicators for dashboard alerts
    risk_indicators: {
      volatility_level: CASE risk_profile
        WHEN 'low' THEN 'stable'
        WHEN 'high' THEN 'volatile'
        ELSE 'moderate'
      END,
      
      seasonal_impact: CASE 
        WHEN include_seasonality AND projection_date.month IN [11, 12] THEN 'positive_seasonal'
        WHEN include_seasonality AND projection_date.month IN [1, 7] THEN 'negative_seasonal'
        ELSE 'neutral'
      END,
      
      projection_variance: round(
        (confidence_params.upper_multiplier - confidence_params.lower_multiplier) * 100, 1
      )
    },
    
    // Dashboard refresh and caching hints
    dashboard_hints: {
      refresh_frequency: CASE 
        WHEN projection_date <= date_add(base_date, duration({months: 1})) THEN 'daily'
        WHEN projection_date <= date_add(base_date, duration({months: 3})) THEN 'weekly'
        ELSE 'monthly'
      END,
      cache_duration: 1800, // 30 minutes
      last_updated: timestamp()
    }
  } as projection_metadata

ORDER BY projection_date;