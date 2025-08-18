/**
 * Partner Contribution Aggregation Template
 * 
 * Aggregates and analyzes partner contributions across multiple dimensions,
 * providing comprehensive insights into partner value, performance, and impact.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for aggregating partner contribution metrics across revenue, customers, and strategic value
 */
export class PartnerContributionAggregationTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'aggregate_partner_contribution',
      'Aggregate comprehensive partner contribution metrics including revenue share, customer acquisition, retention impact, and strategic value for executive partner management',
      'aggregation',
      [
        ...TemplateHelpers.createDateRange('analysis'),
        TemplateHelpers.createParameter(
          'partner_tiers',
          'array',
          'Partner tiers to analyze (optional - if not provided, includes all tiers)',
          {
            required: false,
            examples: [['Gold', 'Platinum'], ['All'], ['Silver', 'Bronze']]
          }
        ),
        TemplateHelpers.createParameter(
          'min_revenue_threshold',
          'decimal',
          'Minimum revenue threshold for partner inclusion in analysis',
          {
            required: false,
            min: 0,
            default: 1000,
            examples: [500, 1000, 5000, 10000]
          }
        ),
        TemplateHelpers.createParameter(
          'contribution_categories',
          'array',
          'Categories of contribution to analyze',
          {
            required: false,
            default: ['revenue', 'customers', 'retention', 'products'],
            examples: [
              ['revenue', 'customers'],
              ['revenue', 'customers', 'retention', 'products'],
              ['strategic', 'operational']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'include_growth_metrics',
          'boolean',
          'Include partner growth and momentum indicators',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'benchmark_against_average',
          'boolean',
          'Include benchmark comparisons against partner tier averages',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'top_n_partners',
          'number',
          'Limit results to top N contributors (optional - if not provided, includes all partners)',
          {
            required: false,
            min: 1,
            max: 100,
            examples: [10, 25, 50, 100]
          }
        ),
        TemplateHelpers.createParameter(
          'strategic_weight_revenue',
          'decimal',
          'Weight factor for revenue contribution in strategic scoring (0-1)',
          {
            required: false,
            min: 0,
            max: 1,
            default: 0.40,
            examples: [0.30, 0.40, 0.50]
          }
        ),
        TemplateHelpers.createParameter(
          'strategic_weight_customers',
          'decimal',
          'Weight factor for customer contribution in strategic scoring (0-1)',
          {
            required: false,
            min: 0,
            max: 1,
            default: 0.30,
            examples: [0.25, 0.30, 0.35]
          }
        ),
        TemplateHelpers.createParameter(
          'strategic_weight_retention',
          'decimal',
          'Weight factor for retention contribution in strategic scoring (0-1)',
          {
            required: false,
            min: 0,
            max: 1,
            default: 0.30,
            examples: [0.20, 0.30, 0.40]
          }
        )
      ],
      {
        painPoint: 'Executives need comprehensive visibility into partner contributions beyond just revenue to make strategic decisions about partner relationships, investment allocation, and program optimization, but lack consolidated multi-dimensional partner value analysis',
        tags: ['partners', 'contribution', 'aggregation', 'strategic-value', 'performance', 'executive', 'roi', 'growth']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      analysis_start,
      analysis_end,
      partner_tiers,
      min_revenue_threshold,
      contribution_categories,
      include_growth_metrics,
      benchmark_against_average,
      top_n_partners,
      strategic_weight_revenue,
      strategic_weight_customers,
      strategic_weight_retention
    } = params;

    let query = `
// Partner Contribution Analysis - Comprehensive Multi-Dimensional View
MATCH (partner:Partner)`;

    // Add partner tier filter if provided
    if (partner_tiers && partner_tiers.length > 0 && !partner_tiers.includes('All')) {
      const tierList = partner_tiers.map((tier: string) => `'${this.escapeString(tier)}'`).join(', ');
      query += `\nWHERE partner.tier IN [${tierList}]`;
    }

    query += `

// Calculate revenue contribution
OPTIONAL MATCH (partner)-[:GENERATES]->(transaction:Transaction)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(analysis_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(analysis_end)}')

// Calculate customer contribution
OPTIONAL MATCH (partner)-[:REFERS]->(customer:Customer)
WHERE customer.created_at >= timestamp('${this.formatDateTime(analysis_start)}')
  AND customer.created_at <= timestamp('${this.formatDateTime(analysis_end)}')

// Calculate customer retention impact
OPTIONAL MATCH (partner)-[:REFERS]->(retained_customer:Customer)
WHERE retained_customer.created_at < timestamp('${this.formatDateTime(analysis_start)}')
  AND retained_customer.last_activity >= timestamp('${this.formatDateTime(analysis_start)}')

// Calculate product engagement
OPTIONAL MATCH (partner)-[:OFFERS]->(product:Product)
OPTIONAL MATCH (partner_transaction:Transaction)-[:FOR_PRODUCT]->(product)
WHERE partner_transaction.transaction_date >= date('${this.formatDate(analysis_start)}')
  AND partner_transaction.transaction_date <= date('${this.formatDate(analysis_end)}')
  AND partner_transaction.status = 'confirmed'

// Aggregate core contribution metrics
WITH partner,
  // Revenue metrics
  COUNT(DISTINCT transaction) AS total_transactions,
  COALESCE(SUM(transaction.amount), 0) AS total_revenue,
  COALESCE(AVG(transaction.amount), 0) AS avg_transaction_value,
  
  // Customer metrics
  COUNT(DISTINCT customer) AS new_customers_acquired,
  COUNT(DISTINCT retained_customer) AS customers_retained,
  
  // Product engagement metrics
  COUNT(DISTINCT product) AS products_offered,
  COUNT(DISTINCT partner_transaction) AS product_transactions,
  COALESCE(SUM(partner_transaction.amount), 0) AS product_revenue

// Filter by minimum revenue threshold
WHERE total_revenue >= ${min_revenue_threshold}`;

    // Add growth metrics calculation if requested
    if (include_growth_metrics) {
      query += `

// Calculate growth metrics by comparing to previous period
OPTIONAL MATCH (partner)-[:GENERATES]->(prev_transaction:Transaction)
WHERE prev_transaction.status = 'confirmed'
  AND prev_transaction.transaction_date >= date('${this.formatDate(analysis_start)}') - duration({months: 6})
  AND prev_transaction.transaction_date < date('${this.formatDate(analysis_start)}')

OPTIONAL MATCH (partner)-[:REFERS]->(prev_customer:Customer)
WHERE prev_customer.created_at >= timestamp('${this.formatDateTime(analysis_start)}') - duration({months: 6})
  AND prev_customer.created_at < timestamp('${this.formatDateTime(analysis_start)}')

WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered, 
  product_transactions, product_revenue,
  
  // Previous period metrics
  COALESCE(SUM(prev_transaction.amount), 0) AS prev_period_revenue,
  COUNT(DISTINCT prev_customer) AS prev_period_customers`;
    }

    query += `

// Calculate contribution percentages and strategic metrics
WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered,
  product_transactions, product_revenue`;

    if (include_growth_metrics) {
      query += `,
  prev_period_revenue, prev_period_customers`;
    }

    // Calculate totals for percentage calculations
    query += `,
  
  // Calculate overall totals for percentage contribution
  reduce(total_revenue_sum = 0.0, p IN collect(total_revenue) | total_revenue_sum + p) AS ecosystem_total_revenue,
  reduce(total_customers_sum = 0, p IN collect(new_customers_acquired) | total_customers_sum + p) AS ecosystem_total_customers

WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered,
  product_transactions, product_revenue`;

    if (include_growth_metrics) {
      query += `,
  prev_period_revenue, prev_period_customers`;
    }

    query += `,
  ecosystem_total_revenue, ecosystem_total_customers,
  
  // Calculate contribution percentages
  CASE WHEN ecosystem_total_revenue > 0 
    THEN (total_revenue / ecosystem_total_revenue) * 100
    ELSE 0 
  END AS revenue_contribution_percent,
  
  CASE WHEN ecosystem_total_customers > 0 
    THEN (toFloat(new_customers_acquired) / ecosystem_total_customers) * 100
    ELSE 0 
  END AS customer_contribution_percent,
  
  // Calculate retention effectiveness
  CASE WHEN customers_retained > 0 AND new_customers_acquired > 0
    THEN (toFloat(customers_retained) / new_customers_acquired) * 100
    ELSE 0
  END AS retention_effectiveness_percent,
  
  // Calculate product engagement score
  CASE WHEN products_offered > 0 
    THEN (toFloat(product_transactions) / products_offered)
    ELSE 0
  END AS product_engagement_score`;

    if (include_growth_metrics) {
      query += `,
  
  // Growth metrics
  CASE WHEN prev_period_revenue > 0 
    THEN ((total_revenue - prev_period_revenue) / prev_period_revenue) * 100
    ELSE 0 
  END AS revenue_growth_percent,
  
  CASE WHEN prev_period_customers > 0 
    THEN ((toFloat(new_customers_acquired - prev_period_customers)) / prev_period_customers) * 100
    ELSE 0 
  END AS customer_growth_percent`;
    }

    query += `

// Calculate strategic value score based on weighted factors
WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered,
  product_transactions, product_revenue, ecosystem_total_revenue,
  revenue_contribution_percent, customer_contribution_percent, 
  retention_effectiveness_percent, product_engagement_score`;

    if (include_growth_metrics) {
      query += `,
  revenue_growth_percent, customer_growth_percent`;
    }

    query += `,
  
  // Normalize metrics to 0-100 scale for strategic scoring
  CASE WHEN revenue_contribution_percent > 50 THEN 100
       WHEN revenue_contribution_percent > 25 THEN 80
       WHEN revenue_contribution_percent > 10 THEN 60
       WHEN revenue_contribution_percent > 5 THEN 40
       ELSE revenue_contribution_percent * 8
  END AS normalized_revenue_score,
  
  CASE WHEN customer_contribution_percent > 30 THEN 100
       WHEN customer_contribution_percent > 15 THEN 80
       WHEN customer_contribution_percent > 8 THEN 60
       WHEN customer_contribution_percent > 3 THEN 40
       ELSE customer_contribution_percent * 12
  END AS normalized_customer_score,
  
  CASE WHEN retention_effectiveness_percent > 90 THEN 100
       WHEN retention_effectiveness_percent > 75 THEN 80
       WHEN retention_effectiveness_percent > 60 THEN 60
       WHEN retention_effectiveness_percent > 45 THEN 40
       ELSE retention_effectiveness_percent * 1.1
  END AS normalized_retention_score

WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered,
  product_transactions, product_revenue, revenue_contribution_percent,
  customer_contribution_percent, retention_effectiveness_percent, 
  product_engagement_score`;

    if (include_growth_metrics) {
      query += `,
  revenue_growth_percent, customer_growth_percent`;
    }

    query += `,
  normalized_revenue_score, normalized_customer_score, normalized_retention_score,
  
  // Calculate composite strategic value score
  (normalized_revenue_score * ${strategic_weight_revenue}) +
  (normalized_customer_score * ${strategic_weight_customers}) +
  (normalized_retention_score * ${strategic_weight_retention}) AS strategic_value_score

// Partner performance classification
WITH partner, total_transactions, total_revenue, avg_transaction_value,
  new_customers_acquired, customers_retained, products_offered,
  product_transactions, product_revenue, revenue_contribution_percent,
  customer_contribution_percent, retention_effectiveness_percent, 
  product_engagement_score`;

    if (include_growth_metrics) {
      query += `,
  revenue_growth_percent, customer_growth_percent`;
    }

    query += `,
  strategic_value_score,
  
  // Partner value tier classification
  CASE 
    WHEN strategic_value_score >= 80 THEN 'Strategic Champion'
    WHEN strategic_value_score >= 65 THEN 'High Value Partner'
    WHEN strategic_value_score >= 45 THEN 'Solid Contributor'
    WHEN strategic_value_score >= 25 THEN 'Developing Partner'
    ELSE 'Underperforming Partner'
  END AS partner_value_tier,
  
  // Contribution balance assessment
  CASE 
    WHEN revenue_contribution_percent > 15 AND customer_contribution_percent > 10 THEN 'Balanced Contributor'
    WHEN revenue_contribution_percent > 20 THEN 'Revenue Driver'
    WHEN customer_contribution_percent > 15 THEN 'Customer Acquisition Leader'
    WHEN retention_effectiveness_percent > 80 THEN 'Retention Specialist'
    ELSE 'Specialized Contributor'
  END AS contribution_profile,
  
  // Investment priority recommendation
  CASE 
    WHEN strategic_value_score >= 70 AND total_revenue >= 50000 THEN 'Invest & Expand'
    WHEN strategic_value_score >= 50 AND total_revenue >= 20000 THEN 'Optimize & Grow'
    WHEN strategic_value_score >= 30 THEN 'Monitor & Develop'
    ELSE 'Evaluate & Decide'
  END AS investment_recommendation`;

    if (benchmark_against_average) {
      query += `

// Calculate tier averages for benchmarking
WITH collect({
  partner: partner,
  tier: partner.tier,
  strategic_score: strategic_value_score,
  revenue: total_revenue,
  customers: new_customers_acquired,
  retention: retention_effectiveness_percent
}) AS all_partners

UNWIND all_partners AS partner_data

WITH partner_data,
  // Calculate tier averages
  avg([p IN all_partners WHERE p.tier = partner_data.tier | p.strategic_score]) AS tier_avg_strategic_score,
  avg([p IN all_partners WHERE p.tier = partner_data.tier | p.revenue]) AS tier_avg_revenue,
  avg([p IN all_partners WHERE p.tier = partner_data.tier | p.customers]) AS tier_avg_customers,
  avg([p IN all_partners WHERE p.tier = partner_data.tier | p.retention]) AS tier_avg_retention

WITH partner_data.partner AS partner,
  partner_data.strategic_score AS strategic_value_score,
  partner_data.revenue AS total_revenue,
  partner_data.customers AS new_customers_acquired,
  partner_data.retention AS retention_effectiveness_percent,
  tier_avg_strategic_score, tier_avg_revenue, tier_avg_customers, tier_avg_retention,
  
  // Performance vs tier average
  CASE WHEN tier_avg_strategic_score > 0 
    THEN ((partner_data.strategic_score - tier_avg_strategic_score) / tier_avg_strategic_score) * 100
    ELSE 0 
  END AS vs_tier_avg_strategic_percent,
  
  CASE WHEN tier_avg_revenue > 0 
    THEN ((partner_data.revenue - tier_avg_revenue) / tier_avg_revenue) * 100
    ELSE 0 
  END AS vs_tier_avg_revenue_percent`;
    }

    // Final output formatting
    query += `

// Final results with executive insights
RETURN 
  partner.code AS partner_id,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  partner.status AS partner_status,
  
  // Core contribution metrics
  total_revenue AS total_contribution_revenue,
  total_transactions AS total_transactions,
  new_customers_acquired AS new_customers_contributed,
  customers_retained AS existing_customers_retained,
  ROUND(avg_transaction_value, 2) AS avg_transaction_value,
  
  // Contribution percentages
  ROUND(revenue_contribution_percent, 2) AS revenue_share_percent,
  ROUND(customer_contribution_percent, 2) AS customer_share_percent,
  ROUND(retention_effectiveness_percent, 2) AS retention_rate_percent,
  
  // Product engagement
  products_offered AS products_in_portfolio,
  product_transactions AS product_related_transactions,
  product_revenue AS product_generated_revenue,
  ROUND(product_engagement_score, 2) AS product_engagement_index,
  
  // Strategic value assessment
  ROUND(strategic_value_score, 1) AS strategic_value_score,
  partner_value_tier AS value_classification,
  contribution_profile AS contribution_type,
  investment_recommendation AS recommended_action`;

    if (include_growth_metrics) {
      query += `,
  
  // Growth indicators
  ROUND(revenue_growth_percent, 2) AS revenue_growth_rate_percent,
  ROUND(customer_growth_percent, 2) AS customer_growth_rate_percent`;
    }

    if (benchmark_against_average) {
      query += `,
  
  // Benchmarking vs tier average
  ROUND(vs_tier_avg_strategic_percent, 1) AS vs_tier_strategic_performance,
  ROUND(vs_tier_avg_revenue_percent, 1) AS vs_tier_revenue_performance`;
    }

    query += `,
  
  // Executive summary flags
  CASE WHEN strategic_value_score >= 80 THEN 'TOP_PERFORMER'
       WHEN strategic_value_score >= 50 THEN 'SOLID_PERFORMER' 
       ELSE 'NEEDS_ATTENTION'
  END AS executive_flag,
  
  '${this.formatDate(analysis_start)}' AS analysis_period_start,
  '${this.formatDate(analysis_end)}' AS analysis_period_end

ORDER BY strategic_value_score DESC, total_revenue DESC`;

    // Apply top N filter if specified
    if (top_n_partners && top_n_partners > 0) {
      query += `\nLIMIT ${top_n_partners}`;
    }

    return query;
  }
}

// Example usage scenarios
export const partnerContributionAggregationExamples = {
  // Comprehensive partner review
  executive_partner_review: {
    name: 'Executive Partner Portfolio Review',
    description: 'Complete partner contribution analysis with strategic scoring and benchmarking',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      min_revenue_threshold: 5000,
      include_growth_metrics: true,
      benchmark_against_average: true,
      top_n_partners: 25,
      strategic_weight_revenue: 0.40,
      strategic_weight_customers: 0.30,
      strategic_weight_retention: 0.30
    }
  },

  // Top tier partner analysis
  strategic_partner_focus: {
    name: 'Strategic Partner Performance Deep Dive',
    description: 'Focus on Gold and Platinum partners with detailed contribution metrics',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      partner_tiers: ['Gold', 'Platinum'],
      min_revenue_threshold: 10000,
      contribution_categories: ['revenue', 'customers', 'retention', 'products'],
      include_growth_metrics: true,
      benchmark_against_average: true,
      strategic_weight_revenue: 0.50,
      strategic_weight_customers: 0.25,
      strategic_weight_retention: 0.25
    }
  },

  // Growth-focused analysis
  growth_partner_identification: {
    name: 'High-Growth Partner Identification',
    description: 'Identify partners with strong growth momentum for increased investment',
    parameters: {
      analysis_start: '2024-06-01',
      analysis_end: '2024-12-31',
      min_revenue_threshold: 1000,
      include_growth_metrics: true,
      benchmark_against_average: false,
      top_n_partners: 50,
      strategic_weight_revenue: 0.35,
      strategic_weight_customers: 0.35,
      strategic_weight_retention: 0.30
    }
  },

  // Underperformer identification
  performance_improvement_focus: {
    name: 'Partner Performance Improvement Opportunities',
    description: 'Identify underperforming partners for development programs',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      min_revenue_threshold: 500,
      include_growth_metrics: true,
      benchmark_against_average: true,
      strategic_weight_revenue: 0.40,
      strategic_weight_customers: 0.30,
      strategic_weight_retention: 0.30
    }
  }
};

// Create and export the template instance
export const partnerContributionAggregationTemplate = new PartnerContributionAggregationTemplate();