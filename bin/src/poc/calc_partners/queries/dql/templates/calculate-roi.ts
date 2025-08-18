/**
 * ROI (Return on Investment) Calculation Template
 * 
 * Calculates return on investment for partner relationships by comparing
 * investment costs (rewards, bonuses, onboarding) against generated revenue.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating ROI on partner investments and partnerships
 */
export class ROICalculationTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_partner_roi',
      'Calculate return on investment (ROI) for partner relationships by analyzing revenue generated versus investment costs over a specified period',
      'analytics',
      [
        TemplateHelpers.createParameter(
          'partner_id',
          'string',
          'Partner ID to calculate ROI for (optional - if not provided, calculates for all partners)',
          {
            required: false,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('analysis'),
        TemplateHelpers.createParameter(
          'include_onboarding_costs',
          'boolean',
          'Whether to include estimated onboarding and setup costs in ROI calculation',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'onboarding_cost_estimate',
          'decimal',
          'Estimated cost per partner for onboarding and setup',
          {
            required: false,
            min: 0,
            default: 500,
            examples: [250, 500, 1000, 2000]
          }
        ),
        TemplateHelpers.createParameter(
          'partner_tier_filter',
          'string',
          'Filter analysis by partner tier level',
          {
            required: false,
            examples: ['bronze', 'silver', 'gold', 'platinum', 'elite']
          }
        ),
        TemplateHelpers.createParameter(
          'min_roi_threshold',
          'decimal',
          'Minimum ROI percentage to include in results (filters out low-performing partners)',
          {
            required: false,
            min: -100,
            max: 1000,
            default: -100,
            examples: [-50, 0, 25, 100]
          }
        ),
        TemplateHelpers.createParameter(
          'include_projected_ltv',
          'boolean',
          'Include projected customer lifetime value in revenue calculations',
          {
            required: false,
            default: false,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'SaaS companies invest heavily in partner programs but lack clear visibility into which partnerships are profitable, making it difficult to optimize partner mix and investment allocation',
        tags: ['roi', 'investment', 'profitability', 'analytics', 'partner-value', 'cost-analysis']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      partner_id,
      analysis_start,
      analysis_end,
      include_onboarding_costs,
      onboarding_cost_estimate,
      partner_tier_filter,
      min_roi_threshold,
      include_projected_ltv
    } = params;

    let query = `
// Calculate Partner ROI Analysis
MATCH (p:Partner)
WHERE p.created_at <= timestamp('${this.formatDateTime(analysis_end)}')`;

    // Add partner ID filter if provided
    if (partner_id) {
      query += `\n  AND p.code = '${this.escapeString(partner_id)}'`;
    }

    // Add partner tier filter if provided
    if (partner_tier_filter) {
      query += `\n  AND p.tier = '${this.escapeString(partner_tier_filter)}'`;
    }

    query += `

// Calculate partner revenue generated in the analysis period
OPTIONAL MATCH (p)-[:GENERATES]->(t:Transaction)
WHERE t.transaction_date >= date('${this.formatDate(analysis_start)}')
  AND t.transaction_date <= date('${this.formatDate(analysis_end)}')
  AND t.status = 'confirmed'

// Calculate rewards/commissions paid to partner in the analysis period
OPTIONAL MATCH (p)<-[:BELONGS_TO]-(r:Reward)
WHERE r.created_at >= timestamp('${this.formatDateTime(analysis_start)}')
  AND r.created_at <= timestamp('${this.formatDateTime(analysis_end)}')
  AND r.status IN ['approved', 'paid']

// Calculate customer acquisition metrics if including LTV
${include_projected_ltv ? `
OPTIONAL MATCH (p)-[:REFERS]->(customers:Partner)
WHERE customers.created_at >= timestamp('${this.formatDateTime(analysis_start)}')
  AND customers.created_at <= timestamp('${this.formatDateTime(analysis_end)}')
` : '// LTV projection disabled'}

// Aggregate financial metrics
WITH p,
  COALESCE(SUM(t.amount), 0) AS revenue_generated,
  COALESCE(COUNT(DISTINCT t), 0) AS transactions_generated,
  COALESCE(SUM(r.amount), 0) AS rewards_paid,
  COALESCE(COUNT(DISTINCT r), 0) AS rewards_count,
  ${include_projected_ltv ? 'COALESCE(COUNT(DISTINCT customers), 0)' : '0'} AS customers_referred

// Calculate investment costs
WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  rewards_paid AS direct_costs,
  CASE WHEN ${include_onboarding_costs} 
    THEN ${onboarding_cost_estimate}
    ELSE 0 
  END AS onboarding_costs

WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  direct_costs, onboarding_costs,
  direct_costs + onboarding_costs AS total_investment

// Calculate projected LTV if enabled
${include_projected_ltv ? `
WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  direct_costs, onboarding_costs, total_investment,
  // Assume average customer LTV of $2000 for projection
  customers_referred * 2000 AS projected_customer_ltv,
  revenue_generated + (customers_referred * 2000) AS total_value_generated
` : `
WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  direct_costs, onboarding_costs, total_investment,
  0 AS projected_customer_ltv,
  revenue_generated AS total_value_generated
`}

// Calculate ROI metrics
WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  direct_costs, onboarding_costs, total_investment, projected_customer_ltv, total_value_generated,
  
  // ROI calculation: (Value Generated - Investment) / Investment * 100
  CASE WHEN total_investment > 0 
    THEN ((total_value_generated - total_investment) / total_investment) * 100
    ELSE CASE WHEN total_value_generated > 0 THEN 999.99 ELSE 0 END
  END AS roi_percentage,
  
  // Profit/Loss
  total_value_generated - total_investment AS net_profit,
  
  // Payback period in months (assuming steady revenue)
  CASE WHEN revenue_generated > 0
    THEN (total_investment / (revenue_generated / 
      DURATION.BETWEEN(date('${this.formatDate(analysis_start)}'), date('${this.formatDate(analysis_end)}')).months + 1))
    ELSE null
  END AS payback_period_months

// Apply ROI threshold filter
WHERE roi_percentage >= ${min_roi_threshold}

// Calculate partner performance categories
WITH p, revenue_generated, transactions_generated, rewards_paid, rewards_count, customers_referred,
  direct_costs, onboarding_costs, total_investment, projected_customer_ltv, total_value_generated,
  roi_percentage, net_profit, payback_period_months,
  
  CASE 
    WHEN roi_percentage >= 200 THEN 'Exceptional'
    WHEN roi_percentage >= 100 THEN 'High Performer'
    WHEN roi_percentage >= 50 THEN 'Strong Performer'
    WHEN roi_percentage >= 0 THEN 'Profitable'
    WHEN roi_percentage >= -25 THEN 'Break-even'
    ELSE 'Loss Making'
  END AS performance_category,
  
  CASE 
    WHEN payback_period_months IS NULL THEN 'No Revenue'
    WHEN payback_period_months <= 3 THEN 'Fast Payback'
    WHEN payback_period_months <= 6 THEN 'Standard Payback'
    WHEN payback_period_months <= 12 THEN 'Slow Payback'
    ELSE 'Very Slow Payback'
  END AS payback_category

RETURN 
  p.code AS partner_id,
  p.name AS partner_name,
  p.tier AS partner_tier,
  p.created_at AS partner_onboard_date,
  
  // Revenue metrics
  revenue_generated AS direct_revenue_generated,
  transactions_generated AS transactions_count,
  projected_customer_ltv AS projected_ltv_value,
  total_value_generated AS total_value_created,
  
  // Cost metrics  
  rewards_paid AS commissions_paid,
  rewards_count AS commission_payments_count,
  onboarding_costs AS estimated_onboarding_cost,
  total_investment AS total_partner_investment,
  
  // ROI analysis
  roi_percentage AS roi_percent,
  net_profit AS net_profit_loss,
  performance_category AS roi_performance_tier,
  payback_period_months AS months_to_payback,
  payback_category AS payback_performance_tier,
  
  // Efficiency metrics
  CASE WHEN transactions_generated > 0 
    THEN (revenue_generated / transactions_generated) 
    ELSE 0 
  END AS avg_transaction_value,
  
  CASE WHEN total_investment > 0 
    THEN (revenue_generated / total_investment) 
    ELSE 0 
  END AS revenue_multiplier,
  
  customers_referred AS customers_acquired,
  '${this.formatDate(analysis_start)}' AS analysis_period_start,
  '${this.formatDate(analysis_end)}' AS analysis_period_end

ORDER BY roi_percentage DESC, total_value_generated DESC`;

    return query;
  }
}

// Example usage scenarios
export const roiCalculationExamples = {
  // Basic ROI analysis for all partners
  basic: {
    name: 'Quarterly Partner ROI Analysis',
    description: 'Calculate ROI for all partners over a quarterly period',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-03-31'
    }
  },

  // Specific partner deep dive with LTV projection
  deep_dive: {
    name: 'Partner Deep Dive with LTV',
    description: 'Comprehensive ROI analysis for a specific partner including projected customer lifetime value',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      include_onboarding_costs: true,
      onboarding_cost_estimate: 1000,
      include_projected_ltv: true
    }
  },

  // High-performing partners only
  top_performers: {
    name: 'Top Performing Partners Analysis',
    description: 'Analyze only partners with positive ROI in premium tiers',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      partner_tier_filter: 'gold',
      min_roi_threshold: 50,
      include_onboarding_costs: true,
      onboarding_cost_estimate: 750
    }
  },

  // Investment optimization analysis
  investment_optimization: {
    name: 'Investment Optimization Analysis',
    description: 'Identify underperforming partnerships for optimization',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      include_onboarding_costs: true,
      onboarding_cost_estimate: 500,
      min_roi_threshold: -50,
      include_projected_ltv: false
    }
  }
};

// Create and export the template instance
export const roiCalculationTemplate = new ROICalculationTemplate();