/**
 * Monthly Revenue Aggregation Template
 * 
 * Aggregates revenue data by month across partners, products, and channels,
 * providing executives with comprehensive revenue trends and performance insights.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for aggregating monthly revenue data across multiple dimensions
 */
export class MonthlyRevenueAggregationTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'aggregate_monthly_revenue',
      'Aggregate monthly revenue data across partners, products, and channels with trend analysis and variance detection for executive reporting',
      'aggregation',
      [
        ...TemplateHelpers.createDateRange('analysis'),
        TemplateHelpers.createParameter(
          'partner_ids',
          'array',
          'Specific partner IDs to include in analysis (optional - if not provided, includes all partners)',
          {
            required: false,
            examples: [['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0'], []]
          }
        ),
        TemplateHelpers.createParameter(
          'product_ids',
          'array',
          'Specific product IDs to include in analysis (optional - if not provided, includes all products)',
          {
            required: false,
            examples: [['PROD_A1B2C3D4', 'PROD_X7Y8Z9W0'], []]
          }
        ),
        TemplateHelpers.createParameter(
          'partner_tiers',
          'array',
          'Partner tiers to include (optional - if not provided, includes all tiers)',
          {
            required: false,
            examples: [['Gold', 'Platinum'], ['Silver', 'Bronze'], ['All']]
          }
        ),
        TemplateHelpers.createParameter(
          'include_forecasting',
          'boolean',
          'Include trend-based revenue forecasting for next 3 months',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'variance_threshold_percent',
          'decimal',
          'Percentage threshold for flagging significant month-over-month variance (as decimal, e.g., 0.15 = 15%)',
          {
            required: false,
            min: 0.01,
            max: 1.0,
            default: 0.20,
            examples: [0.10, 0.15, 0.25, 0.30]
          }
        ),
        TemplateHelpers.createParameter(
          'compare_to_previous_year',
          'boolean',
          'Include year-over-year comparison metrics',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'breakdown_by_channel',
          'boolean',
          'Include channel-level revenue breakdown',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'Executives need comprehensive monthly revenue insights across partners and products with variance detection and forecasting capabilities to make informed strategic decisions, but current reporting lacks aggregation and trend analysis',
        tags: ['revenue', 'aggregation', 'monthly', 'trends', 'executive', 'forecasting', 'variance', 'kpi']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      analysis_start,
      analysis_end,
      partner_ids,
      product_ids,
      partner_tiers,
      include_forecasting,
      variance_threshold_percent,
      compare_to_previous_year,
      breakdown_by_channel
    } = params;

    let query = `
// Monthly Revenue Aggregation and Analysis
MATCH (partner:Partner)-[:OFFERS]->(product:Product)
MATCH (partner)-[:GENERATES]->(transaction:Transaction)
MATCH (transaction)-[:FOR_PRODUCT]->(product)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(analysis_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(analysis_end)}')`;

    // Add partner ID filter if provided
    if (partner_ids && partner_ids.length > 0) {
      const partnerIdList = partner_ids.map((id: string) => `'${this.escapeString(id)}'`).join(', ');
      query += `\n  AND partner.code IN [${partnerIdList}]`;
    }

    // Add product ID filter if provided
    if (product_ids && product_ids.length > 0) {
      const productIdList = product_ids.map((id: string) => `'${this.escapeString(id)}'`).join(', ');
      query += `\n  AND product.code IN [${productIdList}]`;
    }

    // Add partner tier filter if provided
    if (partner_tiers && partner_tiers.length > 0 && !partner_tiers.includes('All')) {
      const tierList = partner_tiers.map((tier: string) => `'${this.escapeString(tier)}'`).join(', ');
      query += `\n  AND partner.tier IN [${tierList}]`;
    }

    query += `

// Extract month-year for aggregation
WITH partner, product, transaction,
  date.truncate('month', transaction.transaction_date) AS month_start,
  toString(transaction.transaction_date.year) + '-' + 
    CASE WHEN transaction.transaction_date.month < 10 
      THEN '0' + toString(transaction.transaction_date.month)
      ELSE toString(transaction.transaction_date.month) 
    END AS month_key`;

    if (breakdown_by_channel) {
      query += `,
  COALESCE(transaction.channel, 'Direct') AS channel`;
    }

    query += `

// Aggregate by month and dimensions
WITH month_start, month_key, partner.tier AS partner_tier, product.category AS product_category`;

    if (breakdown_by_channel) {
      query += `, channel`;
    }

    query += `,
  COUNT(transaction) AS transaction_count,
  SUM(transaction.amount) AS total_revenue,
  AVG(transaction.amount) AS avg_transaction_value,
  COUNT(DISTINCT partner.code) AS unique_partners,
  COUNT(DISTINCT product.code) AS unique_products,
  MIN(transaction.amount) AS min_transaction,
  MAX(transaction.amount) AS max_transaction

// Calculate month-over-month changes
WITH month_start, month_key, partner_tier, product_category`;

    if (breakdown_by_channel) {
      query += `, channel`;
    }

    query += `,
  transaction_count, total_revenue, avg_transaction_value,
  unique_partners, unique_products, min_transaction, max_transaction

ORDER BY month_start

// Collect monthly data for trend analysis
WITH COLLECT({
  month: month_start,
  month_key: month_key,
  tier: partner_tier,
  category: product_category`;

    if (breakdown_by_channel) {
      query += `,
  channel: channel`;
    }

    query += `,
  transaction_count: transaction_count,
  revenue: total_revenue,
  avg_value: avg_transaction_value,
  partners: unique_partners,
  products: unique_products,
  min_transaction: min_transaction,
  max_transaction: max_transaction
}) AS monthly_data

// Calculate overall metrics and trends
UNWIND monthly_data AS month_data
WITH month_data,
  monthly_data,
  
  // Calculate previous month's revenue for variance analysis
  [x IN monthly_data WHERE x.month < month_data.month 
    AND duration.between(x.month, month_data.month).months <= 1][0].revenue AS prev_month_revenue,
  
  // Calculate year-over-year comparison if requested
  ${compare_to_previous_year ? `
  [x IN monthly_data WHERE x.month.year = month_data.month.year - 1 
    AND x.month.month = month_data.month.month][0].revenue AS yoy_revenue,` : ''}
  
  // Calculate moving averages (3-month)
  [x IN monthly_data WHERE x.month <= month_data.month 
    AND duration.between(x.month, month_data.month).months <= 2] AS last_3_months

WITH month_data, monthly_data, prev_month_revenue${compare_to_previous_year ? ', yoy_revenue' : ''}, last_3_months,

  // Month-over-month variance
  CASE WHEN prev_month_revenue IS NOT NULL AND prev_month_revenue > 0
    THEN ((month_data.revenue - prev_month_revenue) / prev_month_revenue)
    ELSE null
  END AS mom_variance_rate,

  ${compare_to_previous_year ? `
  // Year-over-year variance
  CASE WHEN yoy_revenue IS NOT NULL AND yoy_revenue > 0
    THEN ((month_data.revenue - yoy_revenue) / yoy_revenue)
    ELSE null
  END AS yoy_variance_rate,` : ''}

  // 3-month moving average
  CASE WHEN SIZE(last_3_months) > 0
    THEN reduce(total = 0.0, x IN last_3_months | total + x.revenue) / SIZE(last_3_months)
    ELSE month_data.revenue
  END AS moving_avg_3m

// Flag significant variances
WITH month_data, monthly_data, prev_month_revenue${compare_to_previous_year ? ', yoy_revenue' : ''}, 
  mom_variance_rate${compare_to_previous_year ? ', yoy_variance_rate' : ''}, moving_avg_3m,

  // Variance flags
  CASE WHEN ABS(COALESCE(mom_variance_rate, 0)) >= ${variance_threshold_percent}
    THEN 'HIGH_VARIANCE'
    WHEN ABS(COALESCE(mom_variance_rate, 0)) >= ${variance_threshold_percent / 2}
    THEN 'MODERATE_VARIANCE'
    ELSE 'NORMAL'
  END AS variance_flag,

  // Revenue trend classification
  CASE 
    WHEN mom_variance_rate > 0.1 THEN 'STRONG_GROWTH'
    WHEN mom_variance_rate > 0.05 THEN 'MODERATE_GROWTH'
    WHEN mom_variance_rate > -0.05 THEN 'STABLE'
    WHEN mom_variance_rate > -0.1 THEN 'MODERATE_DECLINE'
    ELSE 'DECLINING'
  END AS trend_classification`;

    // Add forecasting calculation if requested
    if (include_forecasting) {
      query += `,

  // Simple linear trend for forecasting (based on last 3 months)
  CASE WHEN SIZE([x IN monthly_data WHERE x.month <= month_data.month 
    AND duration.between(x.month, month_data.month).months <= 2]) >= 2
    THEN (month_data.revenue - 
      [x IN monthly_data WHERE x.month < month_data.month 
        AND duration.between(x.month, month_data.month).months <= 2][0].revenue)
    ELSE 0
  END AS monthly_trend_amount`;
    }

    query += `

// Format final results
WITH month_data,
  mom_variance_rate${compare_to_previous_year ? ', yoy_variance_rate' : ''},
  moving_avg_3m, variance_flag, trend_classification`;

    if (include_forecasting) {
      query += `, monthly_trend_amount`;
    }

    query += `,

  // Create executive summary metrics
  CASE WHEN month_data.revenue >= 1000000 THEN 'High Revenue Month'
       WHEN month_data.revenue >= 500000 THEN 'Strong Revenue Month'
       WHEN month_data.revenue >= 100000 THEN 'Standard Revenue Month'
       ELSE 'Low Revenue Month'
  END AS revenue_performance_tier,

  // Partner performance distribution
  CASE WHEN month_data.partners >= 10 THEN 'High Partner Activity'
       WHEN month_data.partners >= 5 THEN 'Moderate Partner Activity'
       ELSE 'Low Partner Activity'
  END AS partner_activity_level

RETURN 
  month_data.month_key AS month,
  date(month_data.month) AS month_date,
  month_data.tier AS partner_tier,
  month_data.category AS product_category`;

    if (breakdown_by_channel) {
      query += `,
  month_data.channel AS channel`;
    }

    query += `,
  
  // Core revenue metrics
  month_data.revenue AS total_revenue,
  month_data.transaction_count AS total_transactions,
  month_data.avg_value AS avg_transaction_value,
  month_data.partners AS active_partners,
  month_data.products AS active_products,
  
  // Revenue range metrics
  month_data.min_transaction AS min_transaction_amount,
  month_data.max_transaction AS max_transaction_amount,
  
  // Trend analysis
  ROUND(COALESCE(mom_variance_rate * 100, 0), 2) AS mom_change_percent,
  ${compare_to_previous_year ? `ROUND(COALESCE(yoy_variance_rate * 100, 0), 2) AS yoy_change_percent,` : ''}
  ROUND(moving_avg_3m, 2) AS three_month_avg_revenue,
  
  // Classification and flags
  variance_flag AS variance_alert_level,
  trend_classification AS revenue_trend,
  revenue_performance_tier AS monthly_performance_tier,
  partner_activity_level AS partner_engagement_level`;

    if (include_forecasting) {
      query += `,
  
  // Forecasting (next 3 months projection)
  ROUND(month_data.revenue + monthly_trend_amount, 2) AS forecast_next_month,
  ROUND(month_data.revenue + (monthly_trend_amount * 2), 2) AS forecast_month_2,
  ROUND(month_data.revenue + (monthly_trend_amount * 3), 2) AS forecast_month_3,
  'Linear Trend' AS forecast_method`;
    }

    query += `

ORDER BY month_data.month DESC, month_data.tier ASC`;

    if (breakdown_by_channel) {
      query += `, month_data.channel ASC`;
    }

    return query;
  }
}

// Example usage scenarios
export const monthlyRevenueAggregationExamples = {
  // Comprehensive executive dashboard
  executive_dashboard: {
    name: 'Executive Monthly Revenue Dashboard',
    description: 'Complete revenue aggregation with forecasting and variance analysis for C-level reporting',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      include_forecasting: true,
      variance_threshold_percent: 0.15,
      compare_to_previous_year: true,
      breakdown_by_channel: true
    }
  },

  // Specific partner performance
  partner_focus: {
    name: 'Top Partner Revenue Analysis',
    description: 'Focus on specific high-value partners with detailed monthly trends',
    parameters: {
      analysis_start: '2024-06-01',
      analysis_end: '2024-12-31',
      partner_ids: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0'],
      partner_tiers: ['Gold', 'Platinum'],
      include_forecasting: true,
      variance_threshold_percent: 0.10,
      compare_to_previous_year: true,
      breakdown_by_channel: false
    }
  },

  // Product performance focus
  product_analysis: {
    name: 'Product Line Revenue Trends',
    description: 'Monthly revenue aggregation by product category with variance detection',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      product_ids: ['PROD_A1B2C3D4', 'PROD_X7Y8Z9W0'],
      include_forecasting: false,
      variance_threshold_percent: 0.25,
      compare_to_previous_year: true,
      breakdown_by_channel: true
    }
  },

  // Quick monthly summary
  monthly_summary: {
    name: 'Monthly Executive Summary',
    description: 'High-level monthly revenue summary for executive briefings',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      include_forecasting: true,
      variance_threshold_percent: 0.20,
      compare_to_previous_year: false,
      breakdown_by_channel: false
    }
  }
};

// Create and export the template instance
export const monthlyRevenueAggregationTemplate = new MonthlyRevenueAggregationTemplate();