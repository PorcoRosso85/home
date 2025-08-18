/**
 * Partner Performance Analysis Template
 * 
 * Comprehensive partner performance analysis across multiple KPIs and dimensions,
 * providing executives with holistic partner evaluation and strategic insights.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for comprehensive partner performance analysis with multi-dimensional scoring and benchmarking
 */
export class PartnerPerformanceAnalysisTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'analyze_partner_performance',
      'Comprehensive multi-dimensional partner performance analysis including revenue, customer acquisition, retention, engagement, and strategic value scoring for executive decision making',
      'analytics',
      [
        ...TemplateHelpers.createDateRange('performance'),
        TemplateHelpers.createParameter(
          'partner_ids',
          'array',
          'Specific partner IDs to analyze (optional - if not provided, analyzes all partners)',
          {
            required: false,
            examples: [['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0'], []]
          }
        ),
        TemplateHelpers.createParameter(
          'partner_tiers',
          'array',
          'Partner tiers to include in analysis (optional - if not provided, includes all tiers)',
          {
            required: false,
            examples: [['Gold', 'Platinum'], ['All'], ['Silver', 'Bronze']]
          }
        ),
        TemplateHelpers.createParameter(
          'performance_dimensions',
          'array',
          'Performance dimensions to analyze',
          {
            required: false,
            default: ['revenue', 'customers', 'retention', 'engagement', 'growth', 'efficiency'],
            examples: [
              ['revenue', 'customers', 'retention'],
              ['revenue', 'customers', 'retention', 'engagement', 'growth', 'efficiency'],
              ['strategic', 'operational']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'benchmark_calculation',
          'string',
          'Benchmarking method for performance comparison',
          {
            required: false,
            default: 'tier_average',
            examples: ['tier_average', 'top_quartile', 'median', 'custom_targets', 'historical']
          }
        ),
        TemplateHelpers.createParameter(
          'include_trend_analysis',
          'boolean',
          'Include trend analysis and momentum indicators',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'performance_period_comparison',
          'string',
          'Comparison period for trend analysis',
          {
            required: false,
            default: 'previous_period',
            examples: ['previous_period', 'year_over_year', 'quarter_over_quarter', 'none']
          }
        ),
        TemplateHelpers.createParameter(
          'min_activity_threshold',
          'number',
          'Minimum number of transactions required to include partner in analysis',
          {
            required: false,
            min: 1,
            default: 5,
            examples: [1, 5, 10, 25]
          }
        ),
        TemplateHelpers.createParameter(
          'scoring_weights',
          'string',
          'Scoring weights configuration for overall performance score',
          {
            required: false,
            default: 'balanced',
            examples: ['revenue_focused', 'customer_focused', 'balanced', 'growth_focused', 'efficiency_focused']
          }
        ),
        TemplateHelpers.createParameter(
          'alert_thresholds',
          'boolean',
          'Include performance alerts and threshold-based recommendations',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'Executives need comprehensive partner performance analysis across multiple dimensions with benchmarking and trend analysis to make strategic decisions about partner relationships, investments, and program optimization, but lack integrated multi-KPI performance scoring',
        tags: ['performance', 'analysis', 'partners', 'kpi', 'benchmarking', 'trends', 'scoring', 'executive']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      performance_start,
      performance_end,
      partner_ids,
      partner_tiers,
      performance_dimensions,
      benchmark_calculation,
      include_trend_analysis,
      performance_period_comparison,
      min_activity_threshold,
      scoring_weights,
      alert_thresholds
    } = params;

    // Define scoring weights based on configuration
    let weights: Record<string, number>;
    switch (scoring_weights) {
      case 'revenue_focused':
        weights = { revenue: 0.40, customers: 0.20, retention: 0.15, engagement: 0.10, growth: 0.10, efficiency: 0.05 };
        break;
      case 'customer_focused':
        weights = { revenue: 0.20, customers: 0.30, retention: 0.25, engagement: 0.15, growth: 0.05, efficiency: 0.05 };
        break;
      case 'growth_focused':
        weights = { revenue: 0.25, customers: 0.20, retention: 0.15, engagement: 0.10, growth: 0.25, efficiency: 0.05 };
        break;
      case 'efficiency_focused':
        weights = { revenue: 0.25, customers: 0.20, retention: 0.15, engagement: 0.10, growth: 0.10, efficiency: 0.20 };
        break;
      default: // balanced
        weights = { revenue: 0.25, customers: 0.20, retention: 0.20, engagement: 0.15, growth: 0.15, efficiency: 0.05 };
    }

    let query = `
// Partner Performance Analysis - Comprehensive Multi-Dimensional Evaluation
MATCH (partner:Partner)`;

    // Add partner filters
    const filters = [];
    
    if (partner_ids && partner_ids.length > 0) {
      const partnerIdList = partner_ids.map((id: string) => `'${this.escapeString(id)}'`).join(', ');
      filters.push(`partner.code IN [${partnerIdList}]`);
    }

    if (partner_tiers && partner_tiers.length > 0 && !partner_tiers.includes('All')) {
      const tierList = partner_tiers.map((tier: string) => `'${this.escapeString(tier)}'`).join(', ');
      filters.push(`partner.tier IN [${tierList}]`);
    }

    if (filters.length > 0) {
      query += `\nWHERE ${filters.join(' AND ')}`;
    }

    query += `

// Calculate revenue performance metrics
OPTIONAL MATCH (partner)-[:GENERATES]->(transaction:Transaction)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(performance_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(performance_end)}')

// Calculate customer acquisition metrics
OPTIONAL MATCH (partner)-[:REFERS]->(customer:Customer)
WHERE customer.created_at >= timestamp('${this.formatDateTime(performance_start)}')
  AND customer.created_at <= timestamp('${this.formatDateTime(performance_end)}')

// Calculate customer retention metrics (customers acquired before period but still active)
OPTIONAL MATCH (partner)-[:REFERS]->(retained_customer:Customer)
WHERE retained_customer.created_at < timestamp('${this.formatDateTime(performance_start)}')
  AND retained_customer.last_activity >= timestamp('${this.formatDateTime(performance_start)}')
  AND retained_customer.status = 'active'

// Calculate engagement metrics
OPTIONAL MATCH (partner)-[:PARTICIPATES_IN]->(engagement:Engagement)
WHERE engagement.engagement_date >= date('${this.formatDate(performance_start)}')
  AND engagement.engagement_date <= date('${this.formatDate(performance_end)}')

// Calculate product portfolio metrics
OPTIONAL MATCH (partner)-[:OFFERS]->(product:Product)
OPTIONAL MATCH (product_transaction:Transaction)-[:FOR_PRODUCT]->(product)
WHERE product_transaction.status = 'confirmed'
  AND product_transaction.transaction_date >= date('${this.formatDate(performance_start)}')
  AND product_transaction.transaction_date <= date('${this.formatDate(performance_end)}')`;

    // Add trend analysis comparison if requested
    if (include_trend_analysis && performance_period_comparison !== 'none') {
      let comparison_start: string;
      let comparison_end: string;

      switch (performance_period_comparison) {
        case 'previous_period':
          query += `

// Calculate previous period metrics for trend comparison
OPTIONAL MATCH (partner)-[:GENERATES]->(prev_transaction:Transaction)
WHERE prev_transaction.status = 'confirmed'
  AND prev_transaction.transaction_date >= date('${this.formatDate(performance_start)}') - duration.inDays(date('${this.formatDate(performance_end)}'), date('${this.formatDate(performance_start)}'))
  AND prev_transaction.transaction_date < date('${this.formatDate(performance_start)}')

OPTIONAL MATCH (partner)-[:REFERS]->(prev_customer:Customer)
WHERE prev_customer.created_at >= timestamp('${this.formatDateTime(performance_start)}') - duration.inDays(date('${this.formatDate(performance_end)}'), date('${this.formatDate(performance_start)}'))
  AND prev_customer.created_at < timestamp('${this.formatDateTime(performance_start)}')`;
          break;

        case 'year_over_year':
          query += `

// Calculate year-over-year metrics for trend comparison
OPTIONAL MATCH (partner)-[:GENERATES]->(yoy_transaction:Transaction)
WHERE yoy_transaction.status = 'confirmed'
  AND yoy_transaction.transaction_date >= date('${this.formatDate(performance_start)}') - duration({years: 1})
  AND yoy_transaction.transaction_date <= date('${this.formatDate(performance_end)}') - duration({years: 1})

OPTIONAL MATCH (partner)-[:REFERS]->(yoy_customer:Customer)
WHERE yoy_customer.created_at >= timestamp('${this.formatDateTime(performance_start)}') - duration({years: 1})
  AND yoy_customer.created_at <= timestamp('${this.formatDateTime(performance_end)}') - duration({years: 1})`;
          break;

        case 'quarter_over_quarter':
          query += `

// Calculate quarter-over-quarter metrics for trend comparison  
OPTIONAL MATCH (partner)-[:GENERATES]->(qoq_transaction:Transaction)
WHERE qoq_transaction.status = 'confirmed'
  AND qoq_transaction.transaction_date >= date('${this.formatDate(performance_start)}') - duration({months: 3})
  AND qoq_transaction.transaction_date <= date('${this.formatDate(performance_end)}') - duration({months: 3})

OPTIONAL MATCH (partner)-[:REFERS]->(qoq_customer:Customer)
WHERE qoq_customer.created_at >= timestamp('${this.formatDateTime(performance_start)}') - duration({months: 3})
  AND qoq_customer.created_at <= timestamp('${this.formatDateTime(performance_end)}') - duration({months: 3})`;
          break;
      }
    }

    query += `

// Aggregate core performance metrics
WITH partner,
  // Revenue metrics
  COUNT(DISTINCT transaction) AS total_transactions,
  COALESCE(SUM(transaction.amount), 0) AS total_revenue,
  COALESCE(AVG(transaction.amount), 0) AS avg_transaction_value,
  COALESCE(MAX(transaction.amount), 0) AS max_transaction_value,
  
  // Customer metrics
  COUNT(DISTINCT customer) AS new_customers,
  COUNT(DISTINCT retained_customer) AS retained_customers,
  
  // Engagement metrics
  COUNT(DISTINCT engagement) AS engagement_activities,
  
  // Product metrics
  COUNT(DISTINCT product) AS products_offered,
  COUNT(DISTINCT product_transaction) AS product_transactions,
  COALESCE(SUM(product_transaction.amount), 0) AS product_revenue`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      
      query += `,
  
  // Comparison period metrics
  COALESCE(SUM(${prefix}_transaction.amount), 0) AS ${prefix}_revenue,
  COUNT(DISTINCT ${prefix}_customer) AS ${prefix}_customers`;
    }

    query += `

// Filter partners with minimum activity
WHERE total_transactions >= ${min_activity_threshold}

// Calculate performance scores (normalized to 0-100 scale)
WITH partner, total_transactions, total_revenue, avg_transaction_value, max_transaction_value,
  new_customers, retained_customers, engagement_activities, products_offered,
  product_transactions, product_revenue`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      query += `, ${prefix}_revenue, ${prefix}_customers`;
    }

    query += `,
  
  // Revenue performance score (normalized)
  CASE 
    WHEN total_revenue >= 100000 THEN 100
    WHEN total_revenue >= 50000 THEN 85
    WHEN total_revenue >= 25000 THEN 70
    WHEN total_revenue >= 10000 THEN 55
    WHEN total_revenue >= 5000 THEN 40
    WHEN total_revenue >= 1000 THEN 25
    ELSE (total_revenue / 1000.0) * 25
  END AS revenue_score,
  
  // Customer acquisition score (normalized)
  CASE 
    WHEN new_customers >= 50 THEN 100
    WHEN new_customers >= 25 THEN 85
    WHEN new_customers >= 15 THEN 70
    WHEN new_customers >= 10 THEN 55
    WHEN new_customers >= 5 THEN 40
    WHEN new_customers >= 2 THEN 25
    ELSE (toFloat(new_customers) / 2.0) * 25
  END AS customer_score,
  
  // Retention performance score
  CASE 
    WHEN retained_customers >= new_customers * 2 THEN 100
    WHEN retained_customers >= new_customers * 1.5 THEN 85
    WHEN retained_customers >= new_customers THEN 70
    WHEN retained_customers >= new_customers * 0.75 THEN 55
    WHEN retained_customers >= new_customers * 0.5 THEN 40
    WHEN retained_customers >= new_customers * 0.25 THEN 25
    ELSE CASE WHEN new_customers > 0 THEN (toFloat(retained_customers) / new_customers) * 100 ELSE 0 END
  END AS retention_score,
  
  // Engagement activity score
  CASE 
    WHEN engagement_activities >= 20 THEN 100
    WHEN engagement_activities >= 15 THEN 85
    WHEN engagement_activities >= 10 THEN 70
    WHEN engagement_activities >= 7 THEN 55
    WHEN engagement_activities >= 5 THEN 40
    WHEN engagement_activities >= 2 THEN 25
    ELSE (toFloat(engagement_activities) / 2.0) * 25
  END AS engagement_score,
  
  // Efficiency score (revenue per transaction)
  CASE 
    WHEN avg_transaction_value >= 1000 THEN 100
    WHEN avg_transaction_value >= 500 THEN 85
    WHEN avg_transaction_value >= 250 THEN 70
    WHEN avg_transaction_value >= 100 THEN 55
    WHEN avg_transaction_value >= 50 THEN 40
    ELSE (avg_transaction_value / 50.0) * 40
  END AS efficiency_score`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      
      query += `,
  
  // Growth score based on comparison period
  CASE 
    WHEN ${prefix}_revenue = 0 AND total_revenue > 0 THEN 100  // New revenue
    WHEN ${prefix}_revenue > 0 THEN 
      CASE 
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= 0.5 THEN 100
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= 0.25 THEN 85
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= 0.15 THEN 70
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= 0.05 THEN 55
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= -0.05 THEN 40
        WHEN ((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) >= -0.15 THEN 25
        ELSE 10
      END
    ELSE 40  // No comparison data
  END AS growth_score`;
    } else {
      query += `,
  40.0 AS growth_score  // Default when no trend analysis`;
    }

    query += `

// Calculate weighted overall performance score
WITH partner, total_transactions, total_revenue, avg_transaction_value, max_transaction_value,
  new_customers, retained_customers, engagement_activities, products_offered,
  product_transactions, product_revenue, revenue_score, customer_score, 
  retention_score, engagement_score, efficiency_score, growth_score`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      query += `, ${prefix}_revenue, ${prefix}_customers`;
    }

    query += `,
  
  // Calculate weighted composite score
  (revenue_score * ${weights.revenue}) +
  (customer_score * ${weights.customers}) +
  (retention_score * ${weights.retention}) +
  (engagement_score * ${weights.engagement}) +
  (growth_score * ${weights.growth}) +
  (efficiency_score * ${weights.efficiency}) AS overall_performance_score

// Performance tier classification and recommendations
WITH partner, total_transactions, total_revenue, avg_transaction_value, max_transaction_value,
  new_customers, retained_customers, engagement_activities, products_offered,
  product_transactions, product_revenue, revenue_score, customer_score,
  retention_score, engagement_score, efficiency_score, growth_score,
  overall_performance_score`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      query += `, ${prefix}_revenue, ${prefix}_customers`;
    }

    query += `,
  
  // Performance tier classification
  CASE 
    WHEN overall_performance_score >= 85 THEN 'Exceptional Performer'
    WHEN overall_performance_score >= 70 THEN 'Strong Performer'
    WHEN overall_performance_score >= 55 THEN 'Good Performer'
    WHEN overall_performance_score >= 40 THEN 'Average Performer'
    WHEN overall_performance_score >= 25 THEN 'Below Average Performer'
    ELSE 'Underperformer'
  END AS performance_tier,
  
  // Strategic recommendation
  CASE 
    WHEN overall_performance_score >= 80 AND total_revenue >= 50000 THEN 'Invest & Expand Partnership'
    WHEN overall_performance_score >= 70 AND total_revenue >= 25000 THEN 'Optimize & Scale'
    WHEN overall_performance_score >= 55 THEN 'Support & Develop'
    WHEN overall_performance_score >= 40 THEN 'Monitor & Improve'
    WHEN overall_performance_score >= 25 THEN 'Performance Review Required'
    ELSE 'Evaluate Partnership Viability'
  END AS strategic_recommendation,
  
  // Strength identification
  CASE 
    WHEN revenue_score >= 80 THEN 'Revenue Generation'
    WHEN customer_score >= 80 THEN 'Customer Acquisition'
    WHEN retention_score >= 80 THEN 'Customer Retention'
    WHEN engagement_score >= 80 THEN 'Partner Engagement'
    WHEN growth_score >= 80 THEN 'Growth & Momentum'
    WHEN efficiency_score >= 80 THEN 'Operational Efficiency'
    ELSE 'Developing Capabilities'
  END AS primary_strength,
  
  // Improvement area identification
  CASE 
    WHEN revenue_score <= 40 THEN 'Revenue Generation'
    WHEN customer_score <= 40 THEN 'Customer Acquisition'
    WHEN retention_score <= 40 THEN 'Customer Retention'
    WHEN engagement_score <= 40 THEN 'Partner Engagement'
    WHEN growth_score <= 40 THEN 'Growth & Momentum'
    WHEN efficiency_score <= 40 THEN 'Operational Efficiency'
    ELSE 'Balanced Performance'
  END AS improvement_focus`;

    if (alert_thresholds) {
      query += `,
  
  // Performance alerts
  CASE 
    WHEN overall_performance_score < 30 THEN 'CRITICAL_PERFORMANCE'
    WHEN overall_performance_score < 50 AND total_revenue < 5000 THEN 'LOW_PERFORMANCE'
    WHEN growth_score < 25 THEN 'DECLINING_TREND'
    WHEN customer_score < 30 THEN 'CUSTOMER_ACQUISITION_ISSUE'
    WHEN retention_score < 30 THEN 'RETENTION_CONCERN'
    ELSE 'NO_ALERTS'
  END AS performance_alert`;
    }

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      const prefix = performance_period_comparison === 'year_over_year' ? 'yoy' : 
                     performance_period_comparison === 'quarter_over_quarter' ? 'qoq' : 'prev';
      
      query += `,
  
  // Trend calculations
  CASE WHEN ${prefix}_revenue > 0 
    THEN ROUND(((total_revenue - ${prefix}_revenue) / ${prefix}_revenue) * 100, 2)
    ELSE null 
  END AS revenue_trend_percent,
  
  CASE WHEN ${prefix}_customers > 0 
    THEN ROUND(((toFloat(new_customers - ${prefix}_customers)) / ${prefix}_customers) * 100, 2)
    ELSE null 
  END AS customer_trend_percent`;
    }

    // Final results formatting
    query += `

// Format final results for executive reporting
RETURN 
  partner.code AS partner_id,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  partner.status AS partner_status,
  
  // Overall performance metrics
  ROUND(overall_performance_score, 1) AS overall_performance_score,
  performance_tier AS performance_classification,
  strategic_recommendation AS recommended_action,
  primary_strength AS key_strength,
  improvement_focus AS improvement_opportunity,
  
  // Core business metrics
  total_revenue AS total_revenue,
  total_transactions AS total_transactions,
  new_customers AS new_customers_acquired,
  retained_customers AS customers_retained,
  engagement_activities AS engagement_interactions,
  products_offered AS product_portfolio_size,
  ROUND(avg_transaction_value, 2) AS avg_transaction_value,
  
  // Individual dimension scores
  ROUND(revenue_score, 1) AS revenue_performance_score,
  ROUND(customer_score, 1) AS customer_acquisition_score,
  ROUND(retention_score, 1) AS customer_retention_score,
  ROUND(engagement_score, 1) AS partner_engagement_score,
  ROUND(growth_score, 1) AS growth_momentum_score,
  ROUND(efficiency_score, 1) AS operational_efficiency_score`;

    if (include_trend_analysis && performance_period_comparison !== 'none') {
      query += `,
  
  // Trend analysis
  revenue_trend_percent AS revenue_growth_percent,
  customer_trend_percent AS customer_growth_percent,
  '${performance_period_comparison}' AS trend_comparison_basis`;
    }

    if (alert_thresholds) {
      query += `,
  
  // Alerts and flags
  performance_alert AS alert_status`;
    }

    query += `,
  
  // Configuration details
  '${scoring_weights}' AS scoring_method,
  ${min_activity_threshold} AS min_activity_required,
  '${this.formatDate(performance_start)}' AS analysis_period_start,
  '${this.formatDate(performance_end)}' AS analysis_period_end

ORDER BY overall_performance_score DESC, total_revenue DESC`;

    return query;
  }
}

// Example usage scenarios
export const partnerPerformanceAnalysisExamples = {
  // Comprehensive executive review
  executive_performance_review: {
    name: 'Executive Partner Performance Review',
    description: 'Complete multi-dimensional partner performance analysis for executive decision making',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-12-31',
      performance_dimensions: ['revenue', 'customers', 'retention', 'engagement', 'growth', 'efficiency'],
      benchmark_calculation: 'tier_average',
      include_trend_analysis: true,
      performance_period_comparison: 'year_over_year',
      scoring_weights: 'balanced',
      alert_thresholds: true,
      min_activity_threshold: 10
    }
  },

  // Top tier partner focus
  strategic_partner_analysis: {
    name: 'Strategic Partner Deep Dive Analysis',
    description: 'Detailed performance analysis for Gold and Platinum tier partners',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-12-31',
      partner_tiers: ['Gold', 'Platinum'],
      performance_dimensions: ['revenue', 'customers', 'retention', 'engagement', 'growth', 'efficiency'],
      benchmark_calculation: 'top_quartile',
      include_trend_analysis: true,
      performance_period_comparison: 'quarter_over_quarter',
      scoring_weights: 'revenue_focused',
      alert_thresholds: true,
      min_activity_threshold: 15
    }
  },

  // Growth-focused analysis
  growth_performance_analysis: {
    name: 'Partner Growth Performance Analysis',
    description: 'Focus on partner growth metrics and momentum indicators',
    parameters: {
      performance_start: '2024-06-01',
      performance_end: '2024-12-31',
      performance_dimensions: ['revenue', 'customers', 'growth'],
      benchmark_calculation: 'median',
      include_trend_analysis: true,
      performance_period_comparison: 'previous_period',
      scoring_weights: 'growth_focused',
      alert_thresholds: false,
      min_activity_threshold: 5
    }
  },

  // Underperformer identification
  performance_improvement_identification: {
    name: 'Performance Improvement Opportunity Analysis',
    description: 'Identify underperforming partners for development programs',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-12-31',
      performance_dimensions: ['revenue', 'customers', 'retention', 'efficiency'],
      benchmark_calculation: 'tier_average',
      include_trend_analysis: true,
      performance_period_comparison: 'year_over_year',
      scoring_weights: 'balanced',
      alert_thresholds: true,
      min_activity_threshold: 3
    }
  }
};

// Create and export the template instance
export const partnerPerformanceAnalysisTemplate = new PartnerPerformanceAnalysisTemplate();