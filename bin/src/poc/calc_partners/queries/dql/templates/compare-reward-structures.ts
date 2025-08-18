/**
 * Reward Structure Comparison Template
 * 
 * Compares different partner reward structures and their effectiveness,
 * providing executives with insights for optimizing partner incentive programs.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for comparing partner reward structures and analyzing their effectiveness across multiple dimensions
 */
export class RewardStructureComparisonTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'compare_reward_structures',
      'Compare effectiveness of different partner reward structures across tiers, analyze ROI of incentive programs, and optimize reward mechanisms for maximum partner engagement and business outcomes',
      'comparison',
      [
        ...TemplateHelpers.createDateRange('comparison'),
        TemplateHelpers.createParameter(
          'reward_structures',
          'array',
          'Specific reward structures to compare (optional - if not provided, compares all active structures)',
          {
            required: false,
            examples: [
              ['tiered_commission', 'flat_rate', 'performance_bonus'],
              ['revenue_share', 'volume_incentive'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'partner_tiers',
          'array',
          'Partner tiers to include in comparison (optional - if not provided, includes all tiers)',
          {
            required: false,
            examples: [['Gold', 'Platinum'], ['All'], ['Silver', 'Bronze']]
          }
        ),
        TemplateHelpers.createParameter(
          'comparison_metrics',
          'array',
          'Metrics to use for reward structure comparison',
          {
            required: false,
            default: ['roi', 'engagement', 'retention', 'revenue_growth', 'cost_efficiency'],
            examples: [
              ['roi', 'engagement', 'retention'],
              ['revenue_growth', 'cost_efficiency', 'partner_satisfaction'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'include_cost_analysis',
          'boolean',
          'Include comprehensive cost analysis for each reward structure',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'benchmark_baseline',
          'string',
          'Baseline for performance benchmarking',
          {
            required: false,
            default: 'no_reward',
            examples: ['no_reward', 'industry_standard', 'best_performer', 'previous_period']
          }
        ),
        TemplateHelpers.createParameter(
          'reward_attribution_method',
          'string',
          'Method for attributing business outcomes to reward structures',
          {
            required: false,
            default: 'direct',
            examples: ['direct', 'weighted', 'statistical', 'time_weighted']
          }
        ),
        TemplateHelpers.createParameter(
          'min_partner_sample_size',
          'number',
          'Minimum number of partners required per reward structure for meaningful comparison',
          {
            required: false,
            min: 3,
            max: 100,
            default: 10,
            examples: [5, 10, 15, 25]
          }
        ),
        TemplateHelpers.createParameter(
          'statistical_confidence_level',
          'decimal',
          'Statistical confidence level for comparison significance testing (as decimal, e.g., 0.95 = 95%)',
          {
            required: false,
            min: 0.80,
            max: 0.99,
            default: 0.95,
            examples: [0.90, 0.95, 0.99]
          }
        ),
        TemplateHelpers.createParameter(
          'time_lag_consideration',
          'number',
          'Number of months to consider for reward impact lag effect',
          {
            required: false,
            min: 0,
            max: 12,
            default: 3,
            examples: [1, 3, 6, 12]
          }
        )
      ],
      {
        painPoint: 'Partner program managers need to understand which reward structures are most effective at driving partner engagement and business outcomes while maintaining cost efficiency, but lack comparative analysis across different incentive models and their true ROI',
        tags: ['rewards', 'incentives', 'comparison', 'roi', 'partner-programs', 'effectiveness', 'optimization', 'cost-analysis']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      comparison_start,
      comparison_end,
      reward_structures,
      partner_tiers,
      comparison_metrics,
      include_cost_analysis,
      benchmark_baseline,
      reward_attribution_method,
      min_partner_sample_size,
      statistical_confidence_level,
      time_lag_consideration
    } = params;

    let query = `
// Reward Structure Comparison Analysis - Comprehensive Effectiveness and ROI Assessment
MATCH (partner:Partner)`;

    // Add partner tier filter if provided
    if (partner_tiers && partner_tiers.length > 0 && !partner_tiers.includes('All')) {
      const tierList = partner_tiers.map((tier: string) => `'${this.escapeString(tier)}'`).join(', ');
      query += `\nWHERE partner.tier IN [${tierList}]`;
    }

    query += `

// Match partner reward structures and configurations
MATCH (partner)-[:HAS_REWARD_STRUCTURE]->(reward:RewardStructure)`;

    // Add reward structure filter if provided
    if (reward_structures && reward_structures.length > 0 && !reward_structures.includes('all')) {
      const structureList = reward_structures.map((structure: string) => `'${this.escapeString(structure)}'`).join(', ');
      query += `\nWHERE reward.structure_type IN [${structureList}]`;
    }

    query += `

// Calculate partner performance metrics under each reward structure
OPTIONAL MATCH (partner)-[:GENERATES]->(transaction:Transaction)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(comparison_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(comparison_end)}')

// Calculate customer acquisition under reward structure
OPTIONAL MATCH (partner)-[:REFERS]->(customer:Customer)
WHERE customer.created_at >= timestamp('${this.formatDateTime(comparison_start)}')
  AND customer.created_at <= timestamp('${this.formatDateTime(comparison_end)}')

// Calculate partner engagement metrics
OPTIONAL MATCH (partner)-[:PARTICIPATES_IN]->(engagement:Engagement)
WHERE engagement.engagement_date >= date('${this.formatDate(comparison_start)}')
  AND engagement.engagement_date <= date('${this.formatDate(comparison_end)}')`;

    if (include_cost_analysis) {
      query += `

// Calculate reward costs and payouts
OPTIONAL MATCH (reward)-[:GENERATES_COST]->(reward_cost:Cost)
WHERE reward_cost.cost_date >= date('${this.formatDate(comparison_start)}')
  AND reward_cost.cost_date <= date('${this.formatDate(comparison_end)}')
  AND reward_cost.cost_type IN ['commission', 'bonus', 'incentive', 'reward_payout']

OPTIONAL MATCH (partner)-[:RECEIVES_REWARD]->(payout:RewardPayout)
WHERE payout.payout_date >= date('${this.formatDate(comparison_start)}')
  AND payout.payout_date <= date('${this.formatDate(comparison_end)}')`;
    }

    // Add time lag consideration for reward impact
    if (time_lag_consideration > 0) {
      query += `

// Calculate lagged impact metrics (rewards may take time to show effect)
OPTIONAL MATCH (partner)-[:GENERATES]->(lagged_transaction:Transaction)
WHERE lagged_transaction.status = 'confirmed'
  AND lagged_transaction.transaction_date >= date('${this.formatDate(comparison_start)}') + duration({months: ${time_lag_consideration}})
  AND lagged_transaction.transaction_date <= date('${this.formatDate(comparison_end)}') + duration({months: ${time_lag_consideration}})

OPTIONAL MATCH (partner)-[:REFERS]->(lagged_customer:Customer)
WHERE lagged_customer.created_at >= timestamp('${this.formatDateTime(comparison_start)}') + duration({months: ${time_lag_consideration}})
  AND lagged_customer.created_at <= timestamp('${this.formatDateTime(comparison_end)}') + duration({months: ${time_lag_consideration}})`;
    }

    query += `

// Aggregate metrics by reward structure
WITH reward.structure_type AS reward_structure_type,
  reward.tier_applicability AS applicable_tiers,
  reward.base_rate AS base_reward_rate,
  reward.performance_multiplier AS performance_multiplier,
  COUNT(DISTINCT partner) AS partners_under_structure,
  
  // Revenue metrics
  COALESCE(SUM(transaction.amount), 0) AS total_revenue,
  COALESCE(AVG(transaction.amount), 0) AS avg_transaction_value,
  COUNT(DISTINCT transaction) AS total_transactions,
  
  // Customer metrics
  COUNT(DISTINCT customer) AS customers_acquired,
  
  // Engagement metrics
  COUNT(DISTINCT engagement) AS engagement_activities,
  AVG(engagement.score) AS avg_engagement_score`;

    if (include_cost_analysis) {
      query += `,
  
  // Cost metrics
  COALESCE(SUM(reward_cost.amount), 0) AS total_reward_costs,
  COALESCE(SUM(payout.amount), 0) AS total_payouts,
  COALESCE(AVG(payout.amount), 0) AS avg_payout_per_partner`;
    }

    if (time_lag_consideration > 0) {
      query += `,
  
  // Lagged impact metrics
  COALESCE(SUM(lagged_transaction.amount), 0) AS lagged_revenue_impact,
  COUNT(DISTINCT lagged_customer) AS lagged_customer_impact`;
    }

    query += `

// Filter structures with minimum sample size
WHERE partners_under_structure >= ${min_partner_sample_size}

// Calculate effectiveness metrics and ROI
WITH reward_structure_type, applicable_tiers, base_reward_rate, performance_multiplier,
  partners_under_structure, total_revenue, avg_transaction_value, total_transactions,
  customers_acquired, engagement_activities, avg_engagement_score`;

    if (include_cost_analysis) {
      query += `, total_reward_costs, total_payouts, avg_payout_per_partner`;
    }

    if (time_lag_consideration > 0) {
      query += `, lagged_revenue_impact, lagged_customer_impact`;
    }

    query += `,
  
  // Calculate per-partner averages for comparison
  CASE WHEN partners_under_structure > 0 
    THEN total_revenue / partners_under_structure 
    ELSE 0 
  END AS revenue_per_partner,
  
  CASE WHEN partners_under_structure > 0 
    THEN toFloat(customers_acquired) / partners_under_structure 
    ELSE 0 
  END AS customers_per_partner,
  
  CASE WHEN partners_under_structure > 0 
    THEN toFloat(engagement_activities) / partners_under_structure 
    ELSE 0 
  END AS engagement_per_partner`;

    if (include_cost_analysis) {
      query += `,
  
  // ROI calculations
  CASE WHEN total_reward_costs > 0 
    THEN ((total_revenue - total_reward_costs) / total_reward_costs) * 100
    ELSE 0 
  END AS reward_roi_percent,
  
  CASE WHEN total_payouts > 0 
    THEN total_revenue / total_payouts 
    ELSE 0 
  END AS revenue_to_payout_ratio,
  
  CASE WHEN partners_under_structure > 0 
    THEN total_reward_costs / partners_under_structure 
    ELSE 0 
  END AS cost_per_partner`;
    }

    query += `

// Calculate comparative effectiveness scores (normalized to 0-100)
WITH reward_structure_type, applicable_tiers, base_reward_rate, performance_multiplier,
  partners_under_structure, total_revenue, revenue_per_partner, customers_per_partner,
  engagement_per_partner, avg_engagement_score`;

    if (include_cost_analysis) {
      query += `, total_reward_costs, total_payouts, reward_roi_percent, 
  revenue_to_payout_ratio, cost_per_partner`;
    }

    if (time_lag_consideration > 0) {
      query += `, lagged_revenue_impact, lagged_customer_impact`;
    }

    query += `,
  
  // Effectiveness scores (normalized to 100-point scale)
  CASE 
    WHEN revenue_per_partner >= 50000 THEN 100
    WHEN revenue_per_partner >= 25000 THEN 85
    WHEN revenue_per_partner >= 10000 THEN 70
    WHEN revenue_per_partner >= 5000 THEN 55
    WHEN revenue_per_partner >= 1000 THEN 40
    ELSE (revenue_per_partner / 1000) * 40
  END AS revenue_effectiveness_score,
  
  CASE 
    WHEN customers_per_partner >= 20 THEN 100
    WHEN customers_per_partner >= 10 THEN 85
    WHEN customers_per_partner >= 6 THEN 70
    WHEN customers_per_partner >= 3 THEN 55
    WHEN customers_per_partner >= 1 THEN 40
    ELSE customers_per_partner * 40
  END AS acquisition_effectiveness_score,
  
  CASE 
    WHEN engagement_per_partner >= 15 THEN 100
    WHEN engagement_per_partner >= 10 THEN 85
    WHEN engagement_per_partner >= 7 THEN 70
    WHEN engagement_per_partner >= 5 THEN 55
    WHEN engagement_per_partner >= 2 THEN 40
    ELSE engagement_per_partner * 20
  END AS engagement_effectiveness_score`;

    if (include_cost_analysis) {
      query += `,
  
  CASE 
    WHEN reward_roi_percent >= 300 THEN 100
    WHEN reward_roi_percent >= 200 THEN 85
    WHEN reward_roi_percent >= 150 THEN 70
    WHEN reward_roi_percent >= 100 THEN 55
    WHEN reward_roi_percent >= 50 THEN 40
    WHEN reward_roi_percent >= 0 THEN 25
    ELSE 10
  END AS cost_efficiency_score`;
    }

    query += `

// Calculate composite effectiveness score based on selected metrics
WITH reward_structure_type, applicable_tiers, base_reward_rate, performance_multiplier,
  partners_under_structure, total_revenue, revenue_per_partner, customers_per_partner,
  engagement_per_partner, revenue_effectiveness_score, acquisition_effectiveness_score,
  engagement_effectiveness_score`;

    if (include_cost_analysis) {
      query += `, total_reward_costs, total_payouts, reward_roi_percent,
  revenue_to_payout_ratio, cost_per_partner, cost_efficiency_score`;
    }

    if (time_lag_consideration > 0) {
      query += `, lagged_revenue_impact, lagged_customer_impact`;
    }

    // Calculate weighted composite score based on comparison metrics
    const metricWeights: Record<string, number> = {};
    if (comparison_metrics.includes('roi') || comparison_metrics.includes('all')) metricWeights.roi = 0.25;
    if (comparison_metrics.includes('engagement') || comparison_metrics.includes('all')) metricWeights.engagement = 0.20;
    if (comparison_metrics.includes('retention') || comparison_metrics.includes('all')) metricWeights.retention = 0.15;
    if (comparison_metrics.includes('revenue_growth') || comparison_metrics.includes('all')) metricWeights.revenue_growth = 0.25;
    if (comparison_metrics.includes('cost_efficiency') || comparison_metrics.includes('all')) metricWeights.cost_efficiency = 0.15;

    query += `,
  
  // Composite effectiveness score (weighted average)
  (revenue_effectiveness_score * 0.30) +
  (acquisition_effectiveness_score * 0.25) +
  (engagement_effectiveness_score * 0.20) +`;

    if (include_cost_analysis) {
      query += `
  (cost_efficiency_score * 0.25)`;
    } else {
      query += `
  (revenue_effectiveness_score * 0.25)`;
    }

    query += ` AS composite_effectiveness_score,
  
  // Structure classification
  CASE 
    WHEN base_reward_rate > 0 AND performance_multiplier > 1 THEN 'Performance-Based Variable'
    WHEN base_reward_rate > 0 AND performance_multiplier <= 1 THEN 'Fixed Rate'
    WHEN performance_multiplier > 1 THEN 'Pure Performance-Based'
    ELSE 'Hybrid Structure'
  END AS structure_classification`;

    // Performance ranking and recommendations
    query += `

// Calculate relative performance rankings and generate recommendations
WITH collect({
  structure: reward_structure_type,
  tiers: applicable_tiers,
  base_rate: base_reward_rate,
  multiplier: performance_multiplier,
  partners: partners_under_structure,
  revenue: total_revenue,
  revenue_per_partner: revenue_per_partner,
  customers_per_partner: customers_per_partner,
  engagement_per_partner: engagement_per_partner,
  revenue_score: revenue_effectiveness_score,
  acquisition_score: acquisition_effectiveness_score,
  engagement_score: engagement_effectiveness_score`;

    if (include_cost_analysis) {
      query += `,
  costs: total_reward_costs,
  payouts: total_payouts,
  roi: reward_roi_percent,
  cost_efficiency: cost_efficiency_score`;
    }

    if (time_lag_consideration > 0) {
      query += `,
  lagged_revenue: lagged_revenue_impact,
  lagged_customers: lagged_customer_impact`;
    }

    query += `,
  composite_score: composite_effectiveness_score,
  classification: structure_classification
}) AS all_structures

UNWIND all_structures AS structure_data

WITH structure_data,
  // Calculate rankings
  rank() OVER (ORDER BY structure_data.composite_score DESC) AS effectiveness_rank,
  rank() OVER (ORDER BY structure_data.revenue_per_partner DESC) AS revenue_rank`;

    if (include_cost_analysis) {
      query += `,
  rank() OVER (ORDER BY structure_data.roi DESC) AS roi_rank,
  rank() OVER (ORDER BY structure_data.cost_efficiency DESC) AS cost_efficiency_rank`;
    }

    query += `,
  
  // Statistical significance indicators (simplified)
  CASE WHEN structure_data.partners >= ${min_partner_sample_size * 2} 
    THEN 'HIGH_CONFIDENCE' 
    WHEN structure_data.partners >= ${min_partner_sample_size} 
    THEN 'MODERATE_CONFIDENCE'
    ELSE 'LOW_CONFIDENCE' 
  END AS statistical_confidence,
  
  // Performance vs average
  avg([s IN all_structures | s.composite_score]) AS avg_composite_score

WITH structure_data, effectiveness_rank`;

    if (include_cost_analysis) {
      query += `, roi_rank, cost_efficiency_rank`;
    }

    query += `, statistical_confidence, avg_composite_score,
  
  // Performance comparison
  structure_data.composite_score - avg_composite_score AS vs_average_difference,
  
  // Improvement recommendations
  CASE 
    WHEN structure_data.composite_score >= 80 THEN 'SCALE_AND_OPTIMIZE'
    WHEN structure_data.composite_score >= 65 THEN 'MAINTAIN_AND_REFINE'
    WHEN structure_data.composite_score >= 45 THEN 'IMPROVE_UNDERPERFORMING_AREAS'
    WHEN structure_data.composite_score >= 25 THEN 'MAJOR_RESTRUCTURE_NEEDED'
    ELSE 'DISCONTINUE_OR_REDESIGN'
  END AS optimization_recommendation

// Final results with comprehensive comparison insights
RETURN 
  structure_data.structure AS reward_structure_type,
  structure_data.classification AS structure_model,
  structure_data.tiers AS applicable_partner_tiers,
  structure_data.base_rate AS base_reward_rate,
  structure_data.multiplier AS performance_multiplier,
  
  // Partner and performance metrics
  structure_data.partners AS partners_using_structure,
  ROUND(structure_data.revenue, 2) AS total_revenue_generated,
  ROUND(structure_data.revenue_per_partner, 2) AS avg_revenue_per_partner,
  ROUND(structure_data.customers_per_partner, 1) AS avg_customers_per_partner,
  ROUND(structure_data.engagement_per_partner, 1) AS avg_engagement_per_partner,
  
  // Effectiveness scores
  ROUND(structure_data.revenue_score, 1) AS revenue_effectiveness_score,
  ROUND(structure_data.acquisition_score, 1) AS customer_acquisition_score,
  ROUND(structure_data.engagement_score, 1) AS partner_engagement_score,
  ROUND(structure_data.composite_score, 1) AS overall_effectiveness_score`;

    if (include_cost_analysis) {
      query += `,
  
  // Cost and ROI metrics
  ROUND(structure_data.costs, 2) AS total_reward_costs,
  ROUND(structure_data.payouts, 2) AS total_partner_payouts,
  ROUND(structure_data.roi, 1) AS reward_program_roi_percent,
  ROUND(structure_data.cost_efficiency, 1) AS cost_efficiency_score`;
    }

    if (time_lag_consideration > 0) {
      query += `,
  
  // Lagged impact analysis
  ROUND(structure_data.lagged_revenue, 2) AS delayed_revenue_impact,
  structure_data.lagged_customers AS delayed_customer_impact`;
    }

    query += `,
  
  // Comparative rankings
  effectiveness_rank AS overall_effectiveness_rank,
  revenue_rank AS revenue_performance_rank`;

    if (include_cost_analysis) {
      query += `,
  roi_rank AS roi_performance_rank,
  cost_efficiency_rank AS cost_efficiency_rank`;
    }

    query += `,
  
  // Statistical and comparative metrics
  statistical_confidence AS confidence_level,
  ROUND(vs_average_difference, 1) AS vs_average_performance,
  optimization_recommendation AS recommended_action,
  
  // Executive insights
  CASE WHEN effectiveness_rank = 1 THEN 'BEST_PERFORMING_STRUCTURE'
       WHEN effectiveness_rank <= 3 THEN 'TOP_TIER_STRUCTURE'
       WHEN vs_average_difference > 5 THEN 'ABOVE_AVERAGE_PERFORMER'
       WHEN vs_average_difference < -5 THEN 'BELOW_AVERAGE_PERFORMER'
       ELSE 'AVERAGE_PERFORMER'
  END AS performance_classification,
  
  CASE WHEN structure_data.composite_score >= 75 AND structure_data.partners >= 20 
         THEN 'EXPAND_TO_MORE_PARTNERS'
       WHEN structure_data.composite_score >= 60 AND effectiveness_rank <= 3 
         THEN 'OPTIMIZE_AND_SCALE'
       WHEN structure_data.composite_score < 40 
         THEN 'REVIEW_OR_DISCONTINUE'
       ELSE 'MONITOR_AND_ADJUST'
  END AS strategic_recommendation,
  
  // Analysis metadata
  ${min_partner_sample_size} AS min_sample_size_required,
  ${time_lag_consideration} AS time_lag_months_considered,
  '${this.formatDate(comparison_start)}' AS analysis_period_start,
  '${this.formatDate(comparison_end)}' AS analysis_period_end

ORDER BY overall_effectiveness_score DESC, total_revenue_generated DESC`;

    return query;
  }
}

// Example usage scenarios
export const rewardStructureComparisonExamples = {
  // Comprehensive reward structure analysis
  executive_reward_optimization: {
    name: 'Executive Reward Structure Optimization',
    description: 'Complete comparison of all reward structures with ROI and effectiveness analysis',
    parameters: {
      comparison_start: '2024-01-01',
      comparison_end: '2024-12-31',
      reward_structures: ['all'],
      comparison_metrics: ['roi', 'engagement', 'retention', 'revenue_growth', 'cost_efficiency'],
      include_cost_analysis: true,
      benchmark_baseline: 'no_reward',
      reward_attribution_method: 'weighted',
      min_partner_sample_size: 10,
      statistical_confidence_level: 0.95,
      time_lag_consideration: 3
    }
  },

  // Tier-specific reward analysis
  tier_based_reward_comparison: {
    name: 'Tier-Based Reward Structure Analysis',
    description: 'Compare reward effectiveness across different partner tiers',
    parameters: {
      comparison_start: '2024-01-01',
      comparison_end: '2024-12-31',
      partner_tiers: ['Gold', 'Platinum'],
      reward_structures: ['tiered_commission', 'performance_bonus', 'revenue_share'],
      comparison_metrics: ['roi', 'engagement', 'revenue_growth'],
      include_cost_analysis: true,
      benchmark_baseline: 'previous_period',
      min_partner_sample_size: 5,
      time_lag_consideration: 2
    }
  },

  // Cost efficiency focus
  cost_efficiency_analysis: {
    name: 'Reward Cost Efficiency Analysis',
    description: 'Focus on cost efficiency and ROI of different reward mechanisms',
    parameters: {
      comparison_start: '2024-01-01',
      comparison_end: '2024-12-31',
      comparison_metrics: ['cost_efficiency', 'roi'],
      include_cost_analysis: true,
      benchmark_baseline: 'industry_standard',
      reward_attribution_method: 'direct',
      min_partner_sample_size: 8,
      statistical_confidence_level: 0.90,
      time_lag_consideration: 1
    }
  },

  // Quarterly reward review
  quarterly_reward_performance: {
    name: 'Quarterly Reward Performance Review',
    description: 'Regular quarterly assessment of reward structure effectiveness',
    parameters: {
      comparison_start: '2024-10-01',
      comparison_end: '2024-12-31',
      reward_structures: ['tiered_commission', 'flat_rate', 'performance_bonus'],
      comparison_metrics: ['engagement', 'revenue_growth', 'cost_efficiency'],
      include_cost_analysis: true,
      benchmark_baseline: 'best_performer',
      min_partner_sample_size: 5,
      time_lag_consideration: 0
    }
  }
};

// Create and export the template instance
export const rewardStructureComparisonTemplate = new RewardStructureComparisonTemplate();