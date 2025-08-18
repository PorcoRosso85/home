/**
 * Product Profitability Comparison Template
 * 
 * Compares profitability across different products and product categories,
 * providing executives with insights for portfolio optimization and strategic decisions.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for comprehensive product profitability comparison across partners, channels, and market segments
 */
export class ProductProfitabilityComparisonTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'compare_product_profitability',
      'Comprehensive product profitability comparison across categories, partners, and channels with margin analysis, cost allocation, and strategic portfolio insights for executive decision making',
      'comparison',
      [
        ...TemplateHelpers.createDateRange('profitability'),
        TemplateHelpers.createParameter(
          'product_categories',
          'array',
          'Product categories to compare (optional - if not provided, compares all categories)',
          {
            required: false,
            examples: [
              ['Software', 'Services', 'Hardware'],
              ['Premium', 'Standard', 'Basic'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'product_ids',
          'array',
          'Specific product IDs to include in comparison (optional - if not provided, includes all products)',
          {
            required: false,
            examples: [['PROD_A1B2C3D4', 'PROD_X7Y8Z9W0'], []]
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
          'profitability_metrics',
          'array',
          'Profitability metrics to analyze and compare',
          {
            required: false,
            default: ['gross_margin', 'net_margin', 'contribution_margin', 'roi', 'revenue_share'],
            examples: [
              ['gross_margin', 'net_margin', 'roi'],
              ['contribution_margin', 'revenue_share', 'growth_rate'],
              ['all']
            ]
          }
        ),
        TemplateHelpers.createParameter(
          'cost_allocation_method',
          'string',
          'Method for allocating costs to products',
          {
            required: false,
            default: 'activity_based',
            examples: ['direct', 'activity_based', 'revenue_based', 'volume_based', 'hybrid']
          }
        ),
        TemplateHelpers.createParameter(
          'include_partner_costs',
          'boolean',
          'Include partner-specific costs (commissions, support, etc.) in profitability calculations',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'include_lifecycle_analysis',
          'boolean',
          'Include product lifecycle stage analysis in profitability assessment',
          {
            required: false,
            default: false,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'segment_by_channels',
          'boolean',
          'Segment profitability analysis by sales/distribution channels',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'minimum_revenue_threshold',
          'decimal',
          'Minimum revenue threshold for products to be included in comparison',
          {
            required: false,
            min: 0,
            default: 1000,
            examples: [500, 1000, 5000, 10000]
          }
        ),
        TemplateHelpers.createParameter(
          'benchmark_comparison',
          'string',
          'Benchmark for profitability comparison',
          {
            required: false,
            default: 'category_average',
            examples: ['category_average', 'top_performer', 'company_average', 'industry_standard']
          }
        ),
        TemplateHelpers.createParameter(
          'profitability_trends',
          'boolean',
          'Include profitability trend analysis over the specified period',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'Product managers and executives need comprehensive profitability analysis across products and categories to optimize portfolio mix, pricing strategies, and resource allocation, but lack integrated cost allocation and comparative profitability insights across channels and partners',
        tags: ['profitability', 'products', 'comparison', 'margins', 'cost-allocation', 'portfolio', 'roi', 'executive']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      profitability_start,
      profitability_end,
      product_categories,
      product_ids,
      partner_tiers,
      profitability_metrics,
      cost_allocation_method,
      include_partner_costs,
      include_lifecycle_analysis,
      segment_by_channels,
      minimum_revenue_threshold,
      benchmark_comparison,
      profitability_trends
    } = params;

    let query = `
// Product Profitability Comparison - Comprehensive Margin and Portfolio Analysis
MATCH (product:Product)`;

    // Build product filters
    const productFilters = [];

    if (product_categories && product_categories.length > 0 && !product_categories.includes('all')) {
      const categoryList = product_categories.map((cat: string) => `'${this.escapeString(cat)}'`).join(', ');
      productFilters.push(`product.category IN [${categoryList}]`);
    }

    if (product_ids && product_ids.length > 0) {
      const productIdList = product_ids.map((id: string) => `'${this.escapeString(id)}'`).join(', ');
      productFilters.push(`product.code IN [${productIdList}]`);
    }

    if (productFilters.length > 0) {
      query += `\nWHERE ${productFilters.join(' AND ')}`;
    }

    query += `

// Match product transactions
MATCH (transaction:Transaction)-[:FOR_PRODUCT]->(product)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date('${this.formatDate(profitability_start)}')
  AND transaction.transaction_date <= date('${this.formatDate(profitability_end)}')

// Get partner and channel context
OPTIONAL MATCH (partner:Partner)-[:GENERATES]->(transaction)`;

    // Add partner tier filter if provided
    if (partner_tiers && partner_tiers.length > 0 && !partner_tiers.includes('All')) {
      const tierList = partner_tiers.map((tier: string) => `'${this.escapeString(tier)}'`).join(', ');
      query += `\nWHERE partner.tier IN [${tierList}]`;
    }

    query += `

// Get customer context for segmentation
OPTIONAL MATCH (transaction)-[:FROM_CUSTOMER]->(customer:Customer)

// Calculate direct product costs
OPTIONAL MATCH (product)-[:HAS_COST]->(direct_cost:Cost)
WHERE direct_cost.cost_type IN ['production', 'manufacturing', 'direct_materials', 'direct_labor']
  AND direct_cost.cost_date >= date('${this.formatDate(profitability_start)}')
  AND direct_cost.cost_date <= date('${this.formatDate(profitability_end)}')`;

    // Include partner costs if requested
    if (include_partner_costs) {
      query += `

// Calculate partner-related costs
OPTIONAL MATCH (partner)-[:INCURS_COST]->(partner_cost:Cost)
WHERE partner_cost.cost_type IN ['commission', 'referral_fee', 'support_cost', 'training_cost']
  AND partner_cost.cost_date >= date('${this.formatDate(profitability_start)}')
  AND partner_cost.cost_date <= date('${this.formatDate(profitability_end)}')
  AND partner_cost.allocated_to_product = product.code`;
    }

    // Include lifecycle analysis if requested
    if (include_lifecycle_analysis) {
      query += `

// Get product lifecycle information
OPTIONAL MATCH (product)-[:IN_LIFECYCLE_STAGE]->(lifecycle:LifecycleStage)`;
    }

    query += `

// Calculate base profitability metrics
WITH product, transaction, partner, customer,
  COALESCE(transaction.channel, 'direct') AS sales_channel,
  COALESCE(customer.segment, 'general') AS customer_segment,
  
  // Revenue calculation
  transaction.amount AS transaction_revenue,
  
  // Direct cost calculation
  COALESCE(SUM(direct_cost.amount), 0) AS allocated_direct_costs`;

    if (include_partner_costs) {
      query += `,
  
  // Partner cost calculation
  COALESCE(SUM(partner_cost.amount), 0) AS allocated_partner_costs`;
    }

    if (include_lifecycle_analysis) {
      query += `,
  
  // Lifecycle stage
  COALESCE(lifecycle.stage, 'mature') AS product_lifecycle_stage`;
    }

    // Calculate profitability trends if requested
    if (profitability_trends) {
      query += `,
  
  // Time-based grouping for trend analysis
  date.truncate('month', transaction.transaction_date) AS transaction_month`;
    }

    query += `

// Aggregate by product and dimensions
WITH product`;

    if (segment_by_channels) {
      query += `, sales_channel`;
    }

    if (include_lifecycle_analysis) {
      query += `, product_lifecycle_stage`;
    }

    if (profitability_trends) {
      query += `, transaction_month`;
    }

    query += `,
  
  // Revenue metrics
  COUNT(transaction) AS total_transactions,
  SUM(transaction_revenue) AS total_revenue,
  AVG(transaction_revenue) AS avg_transaction_value,
  
  // Cost aggregation based on allocation method
  CASE '${cost_allocation_method}'
    WHEN 'direct' THEN SUM(allocated_direct_costs)
    WHEN 'activity_based' THEN SUM(allocated_direct_costs) + 
      (SUM(transaction_revenue) * 0.15)  -- Activity-based overhead allocation
    WHEN 'revenue_based' THEN SUM(allocated_direct_costs) + 
      (SUM(transaction_revenue) * 0.20)  -- Revenue-based allocation  
    WHEN 'volume_based' THEN SUM(allocated_direct_costs) + 
      (COUNT(transaction) * 50)  -- Volume-based allocation
    WHEN 'hybrid' THEN SUM(allocated_direct_costs) + 
      (SUM(transaction_revenue) * 0.10) + (COUNT(transaction) * 25)
    ELSE SUM(allocated_direct_costs)
  END AS total_allocated_costs`;

    if (include_partner_costs) {
      query += `,
  SUM(allocated_partner_costs) AS total_partner_costs`;
    }

    query += `,
  
  // Customer and partner metrics
  COUNT(DISTINCT customer.code) AS unique_customers,
  COUNT(DISTINCT partner.code) AS active_partners

// Filter by minimum revenue threshold
WHERE total_revenue >= ${minimum_revenue_threshold}

// Calculate profitability metrics
WITH product`;

    if (segment_by_channels) {
      query += `, sales_channel`;
    }

    if (include_lifecycle_analysis) {
      query += `, product_lifecycle_stage`;
    }

    if (profitability_trends) {
      query += `, transaction_month`;
    }

    query += `, total_transactions, total_revenue, avg_transaction_value,
  total_allocated_costs, unique_customers, active_partners`;

    if (include_partner_costs) {
      query += `, total_partner_costs`;
    }

    query += `,
  
  // Core profitability calculations
  total_revenue - total_allocated_costs`;

    if (include_partner_costs) {
      query += ` - total_partner_costs`;
    }

    query += ` AS gross_profit,
  
  // Margin calculations
  CASE WHEN total_revenue > 0 
    THEN ((total_revenue - total_allocated_costs`;

    if (include_partner_costs) {
      query += ` - total_partner_costs`;
    }

    query += `) / total_revenue) * 100
    ELSE 0 
  END AS gross_margin_percent,
  
  // Contribution margin (after partner costs but before fixed overhead)
  CASE WHEN total_revenue > 0 
    THEN ((total_revenue - total_allocated_costs`;

    if (include_partner_costs) {
      query += ` - total_partner_costs`;
    }

    query += ` - (total_revenue * 0.05)) / total_revenue) * 100  -- 5% fixed overhead allocation
    ELSE 0 
  END AS contribution_margin_percent,
  
  // Revenue per transaction efficiency
  CASE WHEN total_transactions > 0 
    THEN total_revenue / total_transactions 
    ELSE 0 
  END AS revenue_efficiency,
  
  // Cost per transaction
  CASE WHEN total_transactions > 0 
    THEN (total_allocated_costs`;

    if (include_partner_costs) {
      query += ` + total_partner_costs`;
    }

    query += `) / total_transactions
    ELSE 0 
  END AS cost_per_transaction`;

    query += `

// Calculate comparative metrics and rankings
WITH collect({
  product_code: product.code,
  product_name: product.name,
  product_category: product.category,
  product_tier: COALESCE(product.tier, 'standard')`;

    if (segment_by_channels) {
      query += `,
  channel: sales_channel`;
    }

    if (include_lifecycle_analysis) {
      query += `,
  lifecycle_stage: product_lifecycle_stage`;
    }

    if (profitability_trends) {
      query += `,
  month: transaction_month`;
    }

    query += `,
  transactions: total_transactions,
  revenue: total_revenue,
  avg_transaction: avg_transaction_value,
  allocated_costs: total_allocated_costs`;

    if (include_partner_costs) {
      query += `,
  partner_costs: total_partner_costs`;
    }

    query += `,
  gross_profit: gross_profit,
  gross_margin: gross_margin_percent,
  contribution_margin: contribution_margin_percent,
  revenue_efficiency: revenue_efficiency,
  cost_per_transaction: cost_per_transaction,
  customers: unique_customers,
  partners: active_partners
}) AS product_metrics

UNWIND product_metrics AS metrics

// Calculate benchmarks and relative performance
WITH metrics,
  // Calculate category averages for benchmarking
  avg([m IN product_metrics WHERE m.product_category = metrics.product_category | m.gross_margin]) AS category_avg_margin,
  avg([m IN product_metrics WHERE m.product_category = metrics.product_category | m.revenue]) AS category_avg_revenue,
  avg([m IN product_metrics WHERE m.product_category = metrics.product_category | m.contribution_margin]) AS category_avg_contribution,
  
  // Calculate overall averages
  avg([m IN product_metrics | m.gross_margin]) AS overall_avg_margin,
  avg([m IN product_metrics | m.revenue]) AS overall_avg_revenue,
  max([m IN product_metrics | m.gross_margin]) AS best_margin,
  max([m IN product_metrics | m.revenue]) AS best_revenue

WITH metrics, category_avg_margin, category_avg_revenue, category_avg_contribution,
  overall_avg_margin, overall_avg_revenue, best_margin, best_revenue,
  
  // Performance vs benchmarks
  CASE '${benchmark_comparison}'
    WHEN 'category_average' THEN metrics.gross_margin - category_avg_margin
    WHEN 'top_performer' THEN metrics.gross_margin - best_margin  
    WHEN 'company_average' THEN metrics.gross_margin - overall_avg_margin
    ELSE metrics.gross_margin - overall_avg_margin
  END AS margin_vs_benchmark,
  
  CASE '${benchmark_comparison}'
    WHEN 'category_average' THEN metrics.revenue - category_avg_revenue
    WHEN 'top_performer' THEN metrics.revenue - best_revenue
    WHEN 'company_average' THEN metrics.revenue - overall_avg_revenue  
    ELSE metrics.revenue - overall_avg_revenue
  END AS revenue_vs_benchmark,
  
  // Profitability tier classification
  CASE 
    WHEN metrics.gross_margin >= 60 THEN 'High Profitability'
    WHEN metrics.gross_margin >= 40 THEN 'Good Profitability'
    WHEN metrics.gross_margin >= 20 THEN 'Moderate Profitability'
    WHEN metrics.gross_margin >= 10 THEN 'Low Profitability'
    ELSE 'Unprofitable'
  END AS profitability_tier,
  
  // Strategic classification
  CASE 
    WHEN metrics.gross_margin >= 40 AND metrics.revenue >= 25000 THEN 'Star Product'
    WHEN metrics.gross_margin >= 30 AND metrics.revenue >= 10000 THEN 'Cash Cow'
    WHEN metrics.gross_margin >= 20 AND metrics.revenue <= 5000 THEN 'Question Mark'
    WHEN metrics.gross_margin < 20 THEN 'Problem Product'
    ELSE 'Developing Product'
  END AS strategic_classification,
  
  // Investment recommendation
  CASE 
    WHEN metrics.gross_margin >= 50 AND metrics.revenue >= 20000 THEN 'INVEST_AND_SCALE'
    WHEN metrics.gross_margin >= 30 AND metrics.revenue >= 10000 THEN 'OPTIMIZE_AND_GROW'
    WHEN metrics.gross_margin >= 20 THEN 'MAINTAIN_AND_MONITOR'
    WHEN metrics.gross_margin >= 10 THEN 'IMPROVE_OR_DIVEST'
    ELSE 'DISCONTINUE_OR_REDESIGN'
  END AS investment_recommendation

// Final results with comprehensive profitability insights
RETURN 
  metrics.product_code AS product_id,
  metrics.product_name AS product_name,
  metrics.product_category AS product_category,
  metrics.product_tier AS product_tier`;

    if (segment_by_channels) {
      query += `,
  metrics.channel AS sales_channel`;
    }

    if (include_lifecycle_analysis) {
      query += `,
  metrics.lifecycle_stage AS lifecycle_stage`;
    }

    if (profitability_trends) {
      query += `,
  metrics.month AS analysis_month`;
    }

    query += `,
  
  // Core business metrics
  metrics.transactions AS total_transactions,
  ROUND(metrics.revenue, 2) AS total_revenue,
  ROUND(metrics.avg_transaction, 2) AS avg_transaction_value,
  metrics.customers AS unique_customers_served,
  metrics.partners AS partner_channels_used,
  
  // Cost breakdown
  ROUND(metrics.allocated_costs, 2) AS allocated_product_costs`;

    if (include_partner_costs) {
      query += `,
  ROUND(metrics.partner_costs, 2) AS partner_related_costs`;
    }

    query += `,
  ROUND(metrics.cost_per_transaction, 2) AS cost_per_transaction,
  
  // Profitability metrics
  ROUND(metrics.gross_profit, 2) AS gross_profit_amount,
  ROUND(metrics.gross_margin, 2) AS gross_margin_percent,
  ROUND(metrics.contribution_margin, 2) AS contribution_margin_percent,
  ROUND(metrics.revenue_efficiency, 2) AS revenue_per_transaction,
  
  // Comparative performance
  ROUND(margin_vs_benchmark, 2) AS margin_performance_vs_benchmark,
  ROUND(revenue_vs_benchmark, 2) AS revenue_performance_vs_benchmark,
  profitability_tier AS profitability_classification,
  strategic_classification AS portfolio_position,
  investment_recommendation AS recommended_action,
  
  // Performance indicators
  CASE WHEN metrics.gross_margin >= category_avg_margin + 10 
         THEN 'OUTPERFORMING_CATEGORY'
       WHEN metrics.gross_margin >= category_avg_margin 
         THEN 'ABOVE_CATEGORY_AVERAGE'
       WHEN metrics.gross_margin >= category_avg_margin - 10 
         THEN 'BELOW_CATEGORY_AVERAGE'
       ELSE 'SIGNIFICANTLY_UNDERPERFORMING'
  END AS category_performance_flag,
  
  CASE WHEN metrics.gross_margin >= 50 AND metrics.revenue >= 50000 
         THEN 'TOP_PROFIT_CONTRIBUTOR'
       WHEN metrics.gross_margin >= 30 AND metrics.revenue >= 20000 
         THEN 'SOLID_PROFIT_CONTRIBUTOR'
       WHEN metrics.gross_margin >= 10 
         THEN 'MARGINAL_CONTRIBUTOR'
       ELSE 'PROFIT_DRAIN'
  END AS profit_contribution_level,
  
  // Executive summary
  CASE WHEN metrics.gross_margin < 10 AND metrics.revenue < 5000 
         THEN 'IMMEDIATE_REVIEW_REQUIRED'
       WHEN metrics.gross_margin < 20 AND margin_vs_benchmark < -10 
         THEN 'PERFORMANCE_IMPROVEMENT_NEEDED'
       WHEN metrics.gross_margin >= 40 AND margin_vs_benchmark > 10 
         THEN 'EXPANSION_OPPORTUNITY'
       ELSE 'MONITOR_PERFORMANCE'
  END AS executive_flag,
  
  // Analysis metadata
  '${cost_allocation_method}' AS cost_allocation_method_used,
  '${benchmark_comparison}' AS benchmark_basis,
  '${this.formatDate(profitability_start)}' AS analysis_period_start,
  '${this.formatDate(profitability_end)}' AS analysis_period_end

ORDER BY gross_margin_percent DESC, total_revenue DESC`;

    return query;
  }
}

// Example usage scenarios
export const productProfitabilityComparisonExamples = {
  // Comprehensive product portfolio analysis
  executive_portfolio_review: {
    name: 'Executive Product Portfolio Profitability Review',
    description: 'Complete product profitability analysis across all categories with strategic insights',
    parameters: {
      profitability_start: '2024-01-01',
      profitability_end: '2024-12-31',
      product_categories: ['all'],
      profitability_metrics: ['gross_margin', 'net_margin', 'contribution_margin', 'roi', 'revenue_share'],
      cost_allocation_method: 'activity_based',
      include_partner_costs: true,
      segment_by_channels: true,
      minimum_revenue_threshold: 5000,
      benchmark_comparison: 'category_average',
      profitability_trends: true
    }
  },

  // Category-specific analysis
  category_profitability_deep_dive: {
    name: 'Software Category Profitability Analysis',
    description: 'Detailed profitability comparison within software product category',
    parameters: {
      profitability_start: '2024-01-01',
      profitability_end: '2024-12-31',
      product_categories: ['Software', 'SaaS'],
      profitability_metrics: ['gross_margin', 'contribution_margin', 'roi'],
      cost_allocation_method: 'hybrid',
      include_partner_costs: true,
      include_lifecycle_analysis: true,
      segment_by_channels: true,
      minimum_revenue_threshold: 2000,
      benchmark_comparison: 'top_performer'
    }
  },

  // Channel profitability focus
  channel_product_profitability: {
    name: 'Channel-Based Product Profitability Analysis',
    description: 'Compare product profitability across different sales channels',
    parameters: {
      profitability_start: '2024-01-01',
      profitability_end: '2024-12-31',
      partner_tiers: ['Gold', 'Platinum'],
      profitability_metrics: ['gross_margin', 'contribution_margin', 'cost_efficiency'],
      cost_allocation_method: 'activity_based',
      include_partner_costs: true,
      segment_by_channels: true,
      minimum_revenue_threshold: 10000,
      benchmark_comparison: 'company_average',
      profitability_trends: false
    }
  },

  // Underperformer identification
  unprofitable_product_analysis: {
    name: 'Unprofitable Product Identification',
    description: 'Identify and analyze underperforming products for improvement or discontinuation',
    parameters: {
      profitability_start: '2024-01-01',
      profitability_end: '2024-12-31',
      profitability_metrics: ['gross_margin', 'contribution_margin', 'revenue_share'],
      cost_allocation_method: 'direct',
      include_partner_costs: true,
      minimum_revenue_threshold: 1000,
      benchmark_comparison: 'category_average',
      profitability_trends: true
    }
  }
};

// Create and export the template instance
export const productProfitabilityComparisonTemplate = new ProductProfitabilityComparisonTemplate();