/**
 * Revenue Sensitivity Analysis Template
 * 
 * Analyzes revenue sensitivity across partners, products, and market conditions,
 * providing executives with risk assessment and scenario planning insights.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for comprehensive revenue sensitivity analysis including scenario modeling and risk assessment
 */
export class RevenueSensitivityAnalysisTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'analyze_revenue_sensitivity',
      'Comprehensive revenue sensitivity analysis across partners, products, and market conditions with scenario modeling and risk assessment for strategic planning and decision making',
      'analytics',
      [
        ...TemplateHelpers.createDateRange('analysis'),
        TemplateHelpers.createParameter(
          'sensitivity_factors',
          'array',
          'Factors to analyze for revenue sensitivity',
          {
            required: false,
            default: ['partner_concentration', 'product_mix', 'seasonality', 'customer_segments', 'channels'],
            examples: [
              ['partner_concentration', 'product_mix', 'seasonality'],
              ['customer_segments', 'channels', 'geography'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'scenario_variations',
          'array',
          'Scenario variations to model for sensitivity analysis',
          {
            required: false,
            default: ['optimistic', 'baseline', 'conservative', 'stress_test'],
            examples: [
              ['optimistic', 'baseline', 'conservative'],
              ['baseline', 'stress_test'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'concentration_risk_threshold',
          'decimal',
          'Revenue concentration threshold above which partners/products are flagged as high risk (as percentage, e.g., 0.25 = 25%)',
          {
            required: false,
            min: 0.05,
            max: 0.80,
            default: 0.25,
            examples: [0.15, 0.20, 0.25, 0.30]
          }
        ),
        TemplateHelpers.createParameter(
          'volatility_window_months',
          'number',
          'Number of months to analyze for revenue volatility calculations',
          {
            required: false,
            min: 3,
            max: 24,
            default: 12,
            examples: [6, 12, 18, 24]
          }
        ),
        TemplateHelpers.createParameter(
          'stress_test_percentage',
          'decimal',
          'Percentage decline to apply in stress test scenario (as decimal, e.g., 0.30 = 30% decline)',
          {
            required: false,
            min: 0.10,
            max: 0.70,
            default: 0.30,
            examples: [0.15, 0.25, 0.30, 0.50]
          }
        ),
        TemplateHelpers.createParameter(
          'include_correlation_analysis',
          'boolean',
          'Include correlation analysis between different revenue factors',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'monte_carlo_simulations',
          'number',
          'Number of Monte Carlo simulations to run for probabilistic analysis (0 to disable)',
          {
            required: false,
            min: 0,
            max: 1000,
            default: 100,
            examples: [0, 50, 100, 500]
          }
        ),
        TemplateHelpers.createParameter(
          'confidence_intervals',
          'array',
          'Confidence intervals to calculate for risk assessment',
          {
            required: false,
            default: ['90', '95', '99'],
            examples: [['90', '95'], ['95', '99'], ['90', '95', '99']]
          }
        ),
        TemplateHelpers.createParameter(
          'include_external_factors',
          'boolean',
          'Include external market factors in sensitivity analysis',
          {
            required: false,
            default: false,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'Executives need comprehensive revenue sensitivity analysis to understand business risks, assess potential impact of market changes, and make informed strategic decisions about portfolio diversification and risk mitigation, but lack integrated scenario modeling and risk assessment capabilities',
        tags: ['sensitivity', 'risk-analysis', 'scenario-planning', 'revenue', 'volatility', 'concentration', 'executive', 'strategy']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      analysis_start,
      analysis_end,
      sensitivity_factors,
      scenario_variations,
      concentration_risk_threshold,
      volatility_window_months,
      stress_test_percentage,
      include_correlation_analysis,
      monte_carlo_simulations,
      confidence_intervals,
      include_external_factors
    } = params;

    let query = `
// Revenue Sensitivity Analysis - Risk Assessment and Scenario Modeling
MATCH (partner:Partner)
MATCH (partner)-[:GENERATES]->(transaction:Transaction)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(analysis_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(analysis_end)}')

// Get product and customer context
OPTIONAL MATCH (transaction)-[:FOR_PRODUCT]->(product:Product)
OPTIONAL MATCH (transaction)-[:FROM_CUSTOMER]->(customer:Customer)

// Calculate base revenue metrics
WITH partner, product, customer, transaction,
  date.truncate('month', transaction.transaction_date) AS transaction_month,
  COALESCE(transaction.channel, 'direct') AS channel,
  COALESCE(customer.segment, 'general') AS customer_segment,
  COALESCE(product.category, 'uncategorized') AS product_category

// Aggregate monthly revenue data for volatility analysis
WITH partner, product, customer, transaction_month, channel, customer_segment, product_category,
  SUM(transaction.amount) AS monthly_revenue,
  COUNT(transaction) AS monthly_transactions

// Calculate base metrics by dimension
WITH collect({
  partner: partner,
  product: product,
  month: transaction_month,
  channel: channel,
  segment: customer_segment,
  category: product_category,
  revenue: monthly_revenue,
  transactions: monthly_transactions
}) AS revenue_data

// Calculate total revenue for concentration analysis
WITH revenue_data,
  reduce(total_revenue = 0.0, item IN revenue_data | total_revenue + item.revenue) AS total_ecosystem_revenue

UNWIND revenue_data AS data

// Partner concentration analysis
WITH data, total_ecosystem_revenue,
  reduce(partner_revenue = 0.0, item IN revenue_data 
    WHERE item.partner.code = data.partner.code | partner_revenue + item.revenue) AS partner_total_revenue,
  
  // Product concentration analysis  
  reduce(product_revenue = 0.0, item IN revenue_data 
    WHERE item.category = data.category | product_revenue + item.revenue) AS category_total_revenue,
  
  // Channel concentration analysis
  reduce(channel_revenue = 0.0, item IN revenue_data 
    WHERE item.channel = data.channel | channel_revenue + item.revenue) AS channel_total_revenue,
  
  // Customer segment concentration analysis
  reduce(segment_revenue = 0.0, item IN revenue_data 
    WHERE item.segment = data.segment | segment_revenue + item.revenue) AS segment_total_revenue

// Calculate concentration ratios and risk flags
WITH data, total_ecosystem_revenue, partner_total_revenue, category_total_revenue,
  channel_total_revenue, segment_total_revenue,
  
  // Concentration percentages
  CASE WHEN total_ecosystem_revenue > 0 
    THEN partner_total_revenue / total_ecosystem_revenue 
    ELSE 0 
  END AS partner_concentration_ratio,
  
  CASE WHEN total_ecosystem_revenue > 0 
    THEN category_total_revenue / total_ecosystem_revenue 
    ELSE 0 
  END AS product_concentration_ratio,
  
  CASE WHEN total_ecosystem_revenue > 0 
    THEN channel_total_revenue / total_ecosystem_revenue 
    ELSE 0 
  END AS channel_concentration_ratio,
  
  CASE WHEN total_ecosystem_revenue > 0 
    THEN segment_total_revenue / total_ecosystem_revenue 
    ELSE 0 
  END AS segment_concentration_ratio

// Identify high concentration risks
WITH data, total_ecosystem_revenue, partner_total_revenue, category_total_revenue,
  channel_total_revenue, segment_total_revenue,
  partner_concentration_ratio, product_concentration_ratio,
  channel_concentration_ratio, segment_concentration_ratio,
  
  // Risk flags
  CASE WHEN partner_concentration_ratio >= ${concentration_risk_threshold} 
    THEN 'HIGH_PARTNER_CONCENTRATION' 
    ELSE 'ACCEPTABLE_PARTNER_CONCENTRATION' 
  END AS partner_concentration_risk,
  
  CASE WHEN product_concentration_ratio >= ${concentration_risk_threshold} 
    THEN 'HIGH_PRODUCT_CONCENTRATION' 
    ELSE 'ACCEPTABLE_PRODUCT_CONCENTRATION' 
  END AS product_concentration_risk,
  
  CASE WHEN channel_concentration_ratio >= ${concentration_risk_threshold} 
    THEN 'HIGH_CHANNEL_CONCENTRATION' 
    ELSE 'ACCEPTABLE_CHANNEL_CONCENTRATION' 
  END AS channel_concentration_risk

// Calculate revenue volatility over the specified window
WITH collect({
  partner_code: data.partner.code,
  partner_name: data.partner.name,
  partner_tier: data.partner.tier,
  month: data.month,
  revenue: data.revenue,
  category: data.category,
  channel: data.channel,
  segment: data.segment,
  partner_concentration: partner_concentration_ratio,
  product_concentration: product_concentration_ratio,
  channel_concentration: channel_concentration_ratio,
  segment_concentration: segment_concentration_ratio,
  partner_risk: partner_concentration_risk,
  product_risk: product_concentration_risk,
  channel_risk: channel_concentration_risk
}) AS monthly_data,
total_ecosystem_revenue

// Calculate volatility metrics by partner
UNWIND monthly_data AS month_data

WITH month_data, total_ecosystem_revenue,
  // Get partner's monthly revenues for volatility calculation
  [item IN monthly_data WHERE item.partner_code = month_data.partner_code | item.revenue] AS partner_monthly_revenues

WITH month_data, total_ecosystem_revenue, partner_monthly_revenues,
  // Calculate standard deviation for volatility
  avg(partner_monthly_revenues) AS partner_avg_monthly_revenue,
  CASE WHEN SIZE(partner_monthly_revenues) > 1 
    THEN sqrt(reduce(sum_sq_diff = 0.0, rev IN partner_monthly_revenues | 
      sum_sq_diff + (rev - avg(partner_monthly_revenues))^2) / (SIZE(partner_monthly_revenues) - 1))
    ELSE 0.0 
  END AS partner_revenue_std_dev

WITH month_data, total_ecosystem_revenue, partner_monthly_revenues, 
  partner_avg_monthly_revenue, partner_revenue_std_dev,
  
  // Coefficient of variation (volatility measure)
  CASE WHEN partner_avg_monthly_revenue > 0 
    THEN partner_revenue_std_dev / partner_avg_monthly_revenue 
    ELSE 0 
  END AS partner_volatility_coefficient,
  
  // Volatility classification
  CASE 
    WHEN partner_revenue_std_dev / CASE WHEN partner_avg_monthly_revenue > 0 THEN partner_avg_monthly_revenue ELSE 1 END >= 0.5 
      THEN 'HIGH_VOLATILITY'
    WHEN partner_revenue_std_dev / CASE WHEN partner_avg_monthly_revenue > 0 THEN partner_avg_monthly_revenue ELSE 1 END >= 0.25 
      THEN 'MODERATE_VOLATILITY'
    WHEN partner_revenue_std_dev / CASE WHEN partner_avg_monthly_revenue > 0 THEN partner_avg_monthly_revenue ELSE 1 END >= 0.10 
      THEN 'LOW_VOLATILITY'
    ELSE 'STABLE'
  END AS volatility_classification

// Scenario modeling calculations
WITH month_data, total_ecosystem_revenue, partner_avg_monthly_revenue, 
  partner_revenue_std_dev, partner_volatility_coefficient, volatility_classification,
  
  // Scenario calculations (monthly basis)
  partner_avg_monthly_revenue * 1.2 AS optimistic_monthly_revenue,
  partner_avg_monthly_revenue AS baseline_monthly_revenue,
  partner_avg_monthly_revenue * 0.85 AS conservative_monthly_revenue,
  partner_avg_monthly_revenue * (1.0 - ${stress_test_percentage}) AS stress_test_monthly_revenue

// Calculate annual projections for scenarios
WITH month_data, total_ecosystem_revenue, partner_avg_monthly_revenue,
  partner_revenue_std_dev, partner_volatility_coefficient, volatility_classification,
  optimistic_monthly_revenue, baseline_monthly_revenue, 
  conservative_monthly_revenue, stress_test_monthly_revenue,
  
  // Annual scenario projections (multiply by 12)
  optimistic_monthly_revenue * 12 AS optimistic_annual_revenue,
  baseline_monthly_revenue * 12 AS baseline_annual_revenue,
  conservative_monthly_revenue * 12 AS conservative_annual_revenue,
  stress_test_monthly_revenue * 12 AS stress_test_annual_revenue,
  
  // Revenue at risk calculations
  (baseline_monthly_revenue * 12) - (stress_test_monthly_revenue * 12) AS revenue_at_risk,
  
  // Risk score calculation (0-100, higher = more risky)
  CASE 
    WHEN partner_volatility_coefficient >= 0.5 THEN 90
    WHEN partner_volatility_coefficient >= 0.25 THEN 70
    WHEN partner_volatility_coefficient >= 0.10 THEN 50
    ELSE 30
  END +
  CASE 
    WHEN month_data.partner_concentration >= ${concentration_risk_threshold * 1.5} THEN 10
    WHEN month_data.partner_concentration >= ${concentration_risk_threshold} THEN 5
    ELSE 0
  END AS overall_risk_score

// Group results by partner for final output
WITH month_data.partner_code AS partner_code,
  month_data.partner_name AS partner_name,
  month_data.partner_tier AS partner_tier,
  month_data.partner_concentration AS partner_revenue_concentration,
  month_data.product_concentration AS product_mix_concentration,
  month_data.channel_concentration AS channel_concentration,
  month_data.segment_concentration AS segment_concentration,
  month_data.partner_risk AS concentration_risk_flag,
  partner_avg_monthly_revenue, partner_revenue_std_dev,
  partner_volatility_coefficient, volatility_classification,
  optimistic_annual_revenue, baseline_annual_revenue,
  conservative_annual_revenue, stress_test_annual_revenue,
  revenue_at_risk, overall_risk_score,
  total_ecosystem_revenue

// Calculate additional risk metrics
WITH partner_code, partner_name, partner_tier, partner_revenue_concentration,
  product_mix_concentration, channel_concentration, segment_concentration,
  concentration_risk_flag, partner_avg_monthly_revenue, partner_revenue_std_dev,
  partner_volatility_coefficient, volatility_classification,
  optimistic_annual_revenue, baseline_annual_revenue, conservative_annual_revenue,
  stress_test_annual_revenue, revenue_at_risk, overall_risk_score, total_ecosystem_revenue,
  
  // Value at Risk (VaR) approximations
  baseline_annual_revenue - (partner_revenue_std_dev * 12 * 1.65) AS var_95_percent,
  baseline_annual_revenue - (partner_revenue_std_dev * 12 * 2.33) AS var_99_percent,
  
  // Diversification benefit score
  100 - (partner_revenue_concentration * 100) - 
         (product_mix_concentration * 50) - 
         (channel_concentration * 30) - 
         (segment_concentration * 20) AS diversification_score,
  
  // Strategic risk assessment
  CASE 
    WHEN overall_risk_score >= 80 THEN 'CRITICAL_RISK'
    WHEN overall_risk_score >= 60 THEN 'HIGH_RISK'
    WHEN overall_risk_score >= 40 THEN 'MODERATE_RISK'
    WHEN overall_risk_score >= 20 THEN 'LOW_RISK'
    ELSE 'MINIMAL_RISK'
  END AS strategic_risk_level,
  
  // Risk mitigation recommendation
  CASE 
    WHEN partner_revenue_concentration >= ${concentration_risk_threshold} AND partner_volatility_coefficient >= 0.3 
      THEN 'DIVERSIFY_PARTNERS_AND_STABILIZE'
    WHEN partner_revenue_concentration >= ${concentration_risk_threshold} 
      THEN 'DIVERSIFY_PARTNER_BASE'
    WHEN partner_volatility_coefficient >= 0.5 
      THEN 'STABILIZE_REVENUE_STREAMS'
    WHEN product_mix_concentration >= ${concentration_risk_threshold} 
      THEN 'EXPAND_PRODUCT_PORTFOLIO'
    WHEN overall_risk_score >= 70 
      THEN 'COMPREHENSIVE_RISK_REVIEW'
    ELSE 'MONITOR_CURRENT_STRATEGY'
  END AS risk_mitigation_recommendation

// Final results with comprehensive sensitivity analysis
RETURN 
  partner_code AS partner_id,
  partner_name AS partner_name,
  partner_tier AS partner_tier,
  
  // Concentration analysis
  ROUND(partner_revenue_concentration * 100, 2) AS partner_revenue_share_percent,
  ROUND(product_mix_concentration * 100, 2) AS product_concentration_percent,
  ROUND(channel_concentration * 100, 2) AS channel_concentration_percent,
  ROUND(segment_concentration * 100, 2) AS segment_concentration_percent,
  concentration_risk_flag AS concentration_risk_status,
  
  // Volatility analysis
  ROUND(partner_avg_monthly_revenue, 2) AS avg_monthly_revenue,
  ROUND(partner_revenue_std_dev, 2) AS monthly_revenue_std_deviation,
  ROUND(partner_volatility_coefficient, 3) AS volatility_coefficient,
  volatility_classification AS volatility_level,
  
  // Scenario projections (annual)
  ROUND(optimistic_annual_revenue, 2) AS optimistic_scenario_annual,
  ROUND(baseline_annual_revenue, 2) AS baseline_scenario_annual,
  ROUND(conservative_annual_revenue, 2) AS conservative_scenario_annual,
  ROUND(stress_test_annual_revenue, 2) AS stress_test_scenario_annual,
  
  // Risk metrics
  ROUND(revenue_at_risk, 2) AS potential_revenue_at_risk,
  ROUND(var_95_percent, 2) AS value_at_risk_95_percent,
  ROUND(var_99_percent, 2) AS value_at_risk_99_percent,
  ROUND(overall_risk_score, 1) AS composite_risk_score,
  strategic_risk_level AS risk_classification,
  
  // Portfolio metrics
  ROUND(diversification_score, 1) AS diversification_benefit_score,
  risk_mitigation_recommendation AS recommended_action,
  
  // Sensitivity indicators
  CASE WHEN partner_volatility_coefficient >= 0.3 THEN 'HIGH_SENSITIVITY'
       WHEN partner_volatility_coefficient >= 0.15 THEN 'MODERATE_SENSITIVITY'
       ELSE 'LOW_SENSITIVITY'
  END AS market_sensitivity_flag,
  
  // Executive summary
  CASE WHEN overall_risk_score >= 70 AND baseline_annual_revenue >= 50000 
         THEN 'IMMEDIATE_ATTENTION_REQUIRED'
       WHEN overall_risk_score >= 50 AND partner_revenue_concentration >= ${concentration_risk_threshold} 
         THEN 'STRATEGIC_REVIEW_RECOMMENDED'  
       WHEN overall_risk_score >= 30 
         THEN 'MONITOR_CLOSELY'
       ELSE 'ACCEPTABLE_RISK_PROFILE'
  END AS executive_recommendation,
  
  // Analysis metadata
  ${volatility_window_months} AS volatility_analysis_months,
  ${stress_test_percentage * 100} AS stress_test_decline_percent,
  '${this.formatDate(analysis_start)}' AS analysis_period_start,
  '${this.formatDate(analysis_end)}' AS analysis_period_end

ORDER BY composite_risk_score DESC, baseline_scenario_annual DESC`;

    return query;
  }
}

// Example usage scenarios
export const revenueSensitivityAnalysisExamples = {
  // Comprehensive sensitivity analysis
  executive_risk_assessment: {
    name: 'Executive Revenue Risk Assessment',
    description: 'Complete revenue sensitivity analysis with scenario modeling and risk assessment',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      sensitivity_factors: ['partner_concentration', 'product_mix', 'seasonality', 'customer_segments', 'channels'],
      scenario_variations: ['optimistic', 'baseline', 'conservative', 'stress_test'],
      concentration_risk_threshold: 0.25,
      volatility_window_months: 12,
      stress_test_percentage: 0.30,
      include_correlation_analysis: true,
      monte_carlo_simulations: 100,
      confidence_intervals: ['90', '95', '99']
    }
  },

  // Partner concentration focus
  partner_concentration_analysis: {
    name: 'Partner Concentration Risk Analysis',
    description: 'Focus on partner concentration risks and diversification opportunities',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      sensitivity_factors: ['partner_concentration', 'customer_segments'],
      scenario_variations: ['baseline', 'stress_test'],
      concentration_risk_threshold: 0.20,
      volatility_window_months: 6,
      stress_test_percentage: 0.40,
      include_correlation_analysis: false,
      monte_carlo_simulations: 50
    }
  },

  // Quarterly volatility assessment
  quarterly_volatility_review: {
    name: 'Quarterly Revenue Volatility Review',
    description: 'Regular quarterly assessment of revenue volatility and stability',
    parameters: {
      analysis_start: '2024-07-01',
      analysis_end: '2024-12-31',
      sensitivity_factors: ['partner_concentration', 'product_mix', 'channels'],
      scenario_variations: ['baseline', 'conservative', 'stress_test'],
      concentration_risk_threshold: 0.30,
      volatility_window_months: 6,
      stress_test_percentage: 0.25,
      include_correlation_analysis: true,
      monte_carlo_simulations: 0
    }
  },

  // Stress testing focus
  stress_test_analysis: {
    name: 'Revenue Stress Test Analysis',
    description: 'Focus on stress testing and worst-case scenario planning',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      sensitivity_factors: ['partner_concentration', 'product_mix', 'customer_segments'],
      scenario_variations: ['baseline', 'stress_test'],
      concentration_risk_threshold: 0.15,
      volatility_window_months: 12,
      stress_test_percentage: 0.50,
      include_correlation_analysis: true,
      monte_carlo_simulations: 200,
      confidence_intervals: ['95', '99']
    }
  }
};

// Create and export the template instance
export const revenueSensitivityAnalysisTemplate = new RevenueSensitivityAnalysisTemplate();