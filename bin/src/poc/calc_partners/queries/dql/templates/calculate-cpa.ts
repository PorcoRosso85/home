/**
 * Customer Per Acquisition (CPA) Calculation Template
 * 
 * Calculates comprehensive customer acquisition costs across partners and channels,
 * providing executives with precise CPA metrics and acquisition efficiency analysis.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating customer per acquisition (CPA) costs with detailed breakdown and efficiency metrics
 */
export class CPACalculationTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_cpa_analysis',
      'Calculate customer per acquisition (CPA) costs across partners, channels, and campaigns with comprehensive efficiency analysis and ROI insights for acquisition optimization',
      'analytics',
      [
        ...TemplateHelpers.createDateRange('analysis'),
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
          'channels',
          'array',
          'Acquisition channels to include in analysis (optional - if not provided, includes all channels)',
          {
            required: false,
            examples: [['direct', 'referral', 'affiliate'], ['paid', 'organic'], []]
          }
        ),
        TemplateHelpers.createParameter(
          'include_partner_costs',
          'boolean',
          'Include partner-specific acquisition costs (commissions, bonuses, etc.)',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'include_campaign_costs',
          'boolean',
          'Include campaign and marketing costs in CPA calculations',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'cpa_calculation_method',
          'string',
          'Method for CPA calculation',
          {
            required: false,
            default: 'blended',
            examples: ['direct', 'blended', 'attributed', 'lifetime']
          }
        ),
        TemplateHelpers.createParameter(
          'customer_value_period_days',
          'number',
          'Period in days to calculate customer value for CPA efficiency (e.g., 365 for annual value)',
          {
            required: false,
            min: 30,
            max: 1095,
            default: 365,
            examples: [90, 180, 365, 730]
          }
        ),
        TemplateHelpers.createParameter(
          'quality_score_weights',
          'boolean',
          'Apply quality score weighting to CPA calculations based on customer lifetime value',
          {
            required: false,
            default: false,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'benchmark_threshold_cpa',
          'decimal',
          'CPA threshold for benchmarking efficiency (partners above this are flagged as high-cost)',
          {
            required: false,
            min: 0,
            default: 100,
            examples: [50, 100, 200, 500]
          }
        ),
        TemplateHelpers.createParameter(
          'segment_by_customer_tier',
          'boolean',
          'Segment CPA analysis by customer value tier (high, medium, low value customers)',
          {
            required: false,
            default: false,
            examples: [true, false]
          }
        )
      ],
      {
        painPoint: 'Marketing and partnership teams need precise customer acquisition cost (CPA) analysis across all channels and partners to optimize acquisition spending and identify the most cost-effective acquisition sources, but lack comprehensive CPA calculation with efficiency and ROI insights',
        tags: ['cpa', 'customer-acquisition', 'cost-analysis', 'efficiency', 'roi', 'marketing', 'partners', 'optimization']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      analysis_start,
      analysis_end,
      partner_ids,
      channels,
      include_partner_costs,
      include_campaign_costs,
      cpa_calculation_method,
      customer_value_period_days,
      quality_score_weights,
      benchmark_threshold_cpa,
      segment_by_customer_tier
    } = params;

    let query = `
// Customer Per Acquisition (CPA) Analysis - Comprehensive Cost and Efficiency Metrics
MATCH (partner:Partner)`;

    // Add partner ID filter if provided
    if (partner_ids && partner_ids.length > 0) {
      const partnerIdList = partner_ids.map((id: string) => `'${this.escapeString(id)}'`).join(', ');
      query += `\nWHERE partner.code IN [${partnerIdList}]`;
    }

    query += `

// Find customers acquired by partners in the analysis period
MATCH (partner)-[:REFERS]->(customer:Customer)
WHERE customer.created_at >= timestamp('${this.formatDateTime(analysis_start)}')
  AND customer.created_at <= timestamp('${this.formatDateTime(analysis_end)}')`;

    // Add channel filter if provided
    if (channels && channels.length > 0) {
      const channelList = channels.map((channel: string) => `'${this.escapeString(channel)}'`).join(', ');
      query += `\n  AND COALESCE(customer.acquisition_channel, 'direct') IN [${channelList}]`;
    }

    query += `

// Calculate customer value over specified period
OPTIONAL MATCH (customer)-[:GENERATES]->(transaction:Transaction)
WHERE transaction.status = 'confirmed'
  AND transaction.transaction_date >= date(customer.created_at)
  AND transaction.transaction_date <= date(customer.created_at) + duration({days: ${customer_value_period_days}})`;

    // Include partner costs if requested
    if (include_partner_costs) {
      query += `

// Calculate partner-specific acquisition costs
OPTIONAL MATCH (partner)-[:INCURS_COST]->(partner_cost:Cost)
WHERE partner_cost.cost_type IN ['commission', 'bonus', 'referral_fee', 'acquisition_cost']
  AND partner_cost.cost_date >= date('${this.formatDate(analysis_start)}')
  AND partner_cost.cost_date <= date('${this.formatDate(analysis_end)}')`;
    }

    // Include campaign costs if requested
    if (include_campaign_costs) {
      query += `

// Calculate campaign and marketing costs
OPTIONAL MATCH (partner)-[:PARTICIPATES_IN]->(campaign:Campaign)
OPTIONAL MATCH (campaign)-[:HAS_COST]->(campaign_cost:Cost)
WHERE campaign_cost.cost_date >= date('${this.formatDate(analysis_start)}')
  AND campaign_cost.cost_date <= date('${this.formatDate(analysis_end)}')
  AND campaign_cost.cost_type IN ['advertising', 'marketing', 'promotion', 'campaign']`;
    }

    query += `

// Aggregate customer and cost data
WITH partner, customer, 
  COALESCE(customer.acquisition_channel, 'direct') AS acquisition_channel,
  
  // Customer value calculation
  COALESCE(SUM(transaction.amount), 0) AS customer_value,
  COUNT(transaction) AS customer_transactions,`;

    if (include_partner_costs) {
      query += `
  
  // Partner acquisition costs
  SUM(DISTINCT partner_cost.amount) AS partner_acquisition_costs,`;
    }

    if (include_campaign_costs) {
      query += `
  
  // Campaign acquisition costs  
  SUM(DISTINCT campaign_cost.amount) AS campaign_acquisition_costs,`;
    }

    query += `
  
  // Customer quality indicators
  duration.inDays(customer.created_at, COALESCE(customer.last_activity, now())).days AS customer_tenure_days,
  customer.status AS customer_status`;

    if (segment_by_customer_tier) {
      query += `,
  
  // Customer value tier classification
  CASE 
    WHEN COALESCE(SUM(transaction.amount), 0) >= 1000 THEN 'High Value'
    WHEN COALESCE(SUM(transaction.amount), 0) >= 300 THEN 'Medium Value'
    WHEN COALESCE(SUM(transaction.amount), 0) >= 50 THEN 'Low Value'
    ELSE 'Minimal Value'
  END AS customer_value_tier`;
    }

    query += `

// Calculate total acquisition costs per customer
WITH partner, customer, acquisition_channel, customer_value, customer_transactions,`;

    if (include_partner_costs) {
      query += ` partner_acquisition_costs,`;
    }

    if (include_campaign_costs) {
      query += ` campaign_acquisition_costs,`;
    }

    query += ` customer_tenure_days, customer_status`;

    if (segment_by_customer_tier) {
      query += `, customer_value_tier`;
    }

    query += `,
  
  // Calculate total acquisition cost per customer based on method
  CASE '${cpa_calculation_method}'
    WHEN 'direct' THEN 
      ${include_partner_costs ? 'COALESCE(partner_acquisition_costs, 0)' : '0'}`;

    if (include_campaign_costs && include_partner_costs) {
      query += ` + COALESCE(campaign_acquisition_costs, 0)`;
    } else if (include_campaign_costs) {
      query += `COALESCE(campaign_acquisition_costs, 0)`;
    }

    query += `
    WHEN 'blended' THEN 
      (${include_partner_costs ? 'COALESCE(partner_acquisition_costs, 0)' : '0'}`;

    if (include_campaign_costs) {
      query += ` + COALESCE(campaign_acquisition_costs, 0)`;
    }

    query += `) * 1.2  // Include overhead allocation
    WHEN 'attributed' THEN 
      ${include_partner_costs ? 'COALESCE(partner_acquisition_costs, 0)' : '0'}`;

    if (include_campaign_costs) {
      query += ` + COALESCE(campaign_acquisition_costs, 0)`;
    }

    query += ` + (customer_value * 0.1)  // Attribute portion of customer value as acquisition investment
    WHEN 'lifetime' THEN 
      (${include_partner_costs ? 'COALESCE(partner_acquisition_costs, 0)' : '0'}`;

    if (include_campaign_costs) {
      query += ` + COALESCE(campaign_acquisition_costs, 0)`;
    }

    query += `) + (customer_value * 0.15)  // Include lifetime servicing allocation
    ELSE ${include_partner_costs ? 'COALESCE(partner_acquisition_costs, 0)' : '0'}`;

    if (include_campaign_costs && include_partner_costs) {
      query += ` + COALESCE(campaign_acquisition_costs, 0)`;
    } else if (include_campaign_costs) {
      query += `COALESCE(campaign_acquisition_costs, 0)`;
    }

    query += `
  END AS total_acquisition_cost_per_customer`;

    if (quality_score_weights) {
      query += `,
  
  // Quality score based on customer performance
  CASE 
    WHEN customer_tenure_days >= 365 AND customer_value >= 500 THEN 1.0
    WHEN customer_tenure_days >= 180 AND customer_value >= 200 THEN 0.8
    WHEN customer_tenure_days >= 90 AND customer_value >= 50 THEN 0.6
    WHEN customer_tenure_days >= 30 THEN 0.4
    ELSE 0.2
  END AS customer_quality_score`;
    }

    query += `

// Aggregate by partner and channel for CPA calculation
WITH partner, acquisition_channel`;

    if (segment_by_customer_tier) {
      query += `, customer_value_tier`;
    }

    query += `,
  COUNT(customer) AS customers_acquired,
  AVG(total_acquisition_cost_per_customer) AS avg_acquisition_cost_per_customer,
  SUM(total_acquisition_cost_per_customer) AS total_acquisition_costs,
  AVG(customer_value) AS avg_customer_value,
  SUM(customer_value) AS total_customer_value,
  AVG(customer_transactions) AS avg_customer_transactions,
  AVG(customer_tenure_days) AS avg_customer_tenure_days,
  
  // Cost efficiency metrics
  MIN(total_acquisition_cost_per_customer) AS min_cpa,
  MAX(total_acquisition_cost_per_customer) AS max_cpa,
  PERCENTILE_CONT(total_acquisition_cost_per_customer, 0.5) AS median_cpa`;

    if (quality_score_weights) {
      query += `,
  AVG(customer_quality_score) AS avg_customer_quality_score,
  AVG(total_acquisition_cost_per_customer * customer_quality_score) AS quality_weighted_cpa`;
    }

    query += `,
  
  // Customer status distribution
  COUNT(CASE WHEN customer_status = 'active' THEN 1 END) AS active_customers,
  COUNT(CASE WHEN customer_status = 'churned' THEN 1 END) AS churned_customers

// Calculate CPA efficiency and ROI metrics
WITH partner, acquisition_channel`;

    if (segment_by_customer_tier) {
      query += `, customer_value_tier`;
    }

    query += `, customers_acquired, avg_acquisition_cost_per_customer, 
  total_acquisition_costs, avg_customer_value, total_customer_value,
  avg_customer_transactions, avg_customer_tenure_days, min_cpa, max_cpa, median_cpa,
  active_customers, churned_customers`;

    if (quality_score_weights) {
      query += `, avg_customer_quality_score, quality_weighted_cpa`;
    }

    query += `,
  
  // ROI calculations
  CASE WHEN total_acquisition_costs > 0 
    THEN ((total_customer_value - total_acquisition_costs) / total_acquisition_costs) * 100
    ELSE 0 
  END AS acquisition_roi_percent,
  
  CASE WHEN avg_acquisition_cost_per_customer > 0 
    THEN avg_customer_value / avg_acquisition_cost_per_customer
    ELSE 0 
  END AS value_to_cost_ratio,
  
  // Efficiency flags
  CASE WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa * 0.5} THEN 'HIGHLY_EFFICIENT'
       WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa} THEN 'EFFICIENT'
       WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa * 1.5} THEN 'ACCEPTABLE'
       WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa * 2} THEN 'HIGH_COST'
       ELSE 'VERY_HIGH_COST'
  END AS cpa_efficiency_flag,
  
  // Payback period calculation (months)
  CASE WHEN avg_customer_value > 0 AND avg_customer_transactions > 0
    THEN (avg_acquisition_cost_per_customer / (avg_customer_value / (avg_customer_tenure_days / 30.0)))
    ELSE null
  END AS payback_period_months,
  
  // Customer retention rate
  CASE WHEN customers_acquired > 0 
    THEN (toFloat(active_customers) / customers_acquired) * 100
    ELSE 0 
  END AS customer_retention_rate`;

    // Final results with executive insights
    query += `

// Format results for executive reporting
RETURN 
  partner.code AS partner_id,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  acquisition_channel AS acquisition_channel`;

    if (segment_by_customer_tier) {
      query += `,
  customer_value_tier AS customer_segment`;
    }

    query += `,
  
  // Core CPA metrics
  customers_acquired AS total_customers_acquired,
  ROUND(avg_acquisition_cost_per_customer, 2) AS average_cpa,
  ROUND(median_cpa, 2) AS median_cpa,
  ROUND(min_cpa, 2) AS minimum_cpa,
  ROUND(max_cpa, 2) AS maximum_cpa,
  ROUND(total_acquisition_costs, 2) AS total_acquisition_investment,
  
  // Customer value metrics
  ROUND(avg_customer_value, 2) AS avg_customer_value_${customer_value_period_days}d,
  ROUND(total_customer_value, 2) AS total_customer_value_generated,
  ROUND(avg_customer_transactions, 1) AS avg_transactions_per_customer,
  ROUND(avg_customer_tenure_days, 0) AS avg_customer_tenure_days,
  
  // Efficiency and ROI metrics
  ROUND(acquisition_roi_percent, 1) AS acquisition_roi_percent,
  ROUND(value_to_cost_ratio, 2) AS customer_value_to_cost_ratio,
  ROUND(COALESCE(payback_period_months, 0), 1) AS payback_period_months,
  ROUND(customer_retention_rate, 1) AS retention_rate_percent,
  cpa_efficiency_flag AS cost_efficiency_classification`;

    if (quality_score_weights) {
      query += `,
  ROUND(avg_customer_quality_score, 2) AS avg_customer_quality_score,
  ROUND(quality_weighted_cpa, 2) AS quality_adjusted_cpa`;
    }

    query += `,
  
  // Performance indicators
  active_customers AS currently_active_customers,
  churned_customers AS churned_customers,
  '${cpa_calculation_method}' AS cpa_calculation_method,
  ${customer_value_period_days} AS value_calculation_period_days,
  
  // Executive flags
  CASE WHEN acquisition_roi_percent >= 200 THEN 'EXCELLENT_ROI'
       WHEN acquisition_roi_percent >= 100 THEN 'STRONG_ROI'
       WHEN acquisition_roi_percent >= 50 THEN 'POSITIVE_ROI'
       WHEN acquisition_roi_percent >= 0 THEN 'BREAK_EVEN'
       ELSE 'NEGATIVE_ROI'
  END AS roi_performance_flag,
  
  CASE WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa} 
         AND acquisition_roi_percent >= 100 THEN 'OPTIMIZE_AND_SCALE'
       WHEN avg_acquisition_cost_per_customer <= ${benchmark_threshold_cpa * 1.5} 
         AND acquisition_roi_percent >= 50 THEN 'MONITOR_AND_IMPROVE'
       WHEN acquisition_roi_percent >= 0 THEN 'EVALUATE_EFFICIENCY'
       ELSE 'REVIEW_OR_PAUSE'
  END AS strategic_recommendation,
  
  '${this.formatDate(analysis_start)}' AS analysis_period_start,
  '${this.formatDate(analysis_end)}' AS analysis_period_end

ORDER BY average_cpa ASC, acquisition_roi_percent DESC`;

    return query;
  }
}

// Example usage scenarios
export const cpaCalculationExamples = {
  // Comprehensive CPA analysis
  executive_cpa_dashboard: {
    name: 'Executive CPA Performance Dashboard',
    description: 'Complete CPA analysis across all partners and channels with ROI insights',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      include_partner_costs: true,
      include_campaign_costs: true,
      cpa_calculation_method: 'blended',
      customer_value_period_days: 365,
      benchmark_threshold_cpa: 100,
      segment_by_customer_tier: true
    }
  },

  // Partner-specific CPA analysis
  partner_cpa_deep_dive: {
    name: 'Strategic Partner CPA Analysis',
    description: 'Detailed CPA analysis for specific high-value partners',
    parameters: {
      analysis_start: '2024-06-01',
      analysis_end: '2024-12-31',
      partner_ids: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0'],
      include_partner_costs: true,
      include_campaign_costs: true,
      cpa_calculation_method: 'attributed',
      customer_value_period_days: 180,
      quality_score_weights: true,
      benchmark_threshold_cpa: 150
    }
  },

  // Channel optimization focus
  channel_cpa_optimization: {
    name: 'Acquisition Channel CPA Optimization',
    description: 'Compare CPA efficiency across different acquisition channels',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      channels: ['direct', 'referral', 'affiliate', 'paid'],
      include_partner_costs: true,
      include_campaign_costs: true,
      cpa_calculation_method: 'blended',
      customer_value_period_days: 365,
      benchmark_threshold_cpa: 75,
      segment_by_customer_tier: false
    }
  },

  // Quick CPA assessment
  monthly_cpa_review: {
    name: 'Monthly CPA Performance Review',
    description: 'Quick monthly assessment of CPA performance trends',
    parameters: {
      analysis_start: '2024-11-01',
      analysis_end: '2024-11-30',
      include_partner_costs: true,
      include_campaign_costs: false,
      cpa_calculation_method: 'direct',
      customer_value_period_days: 90,
      benchmark_threshold_cpa: 120,
      segment_by_customer_tier: false
    }
  }
};

// Create and export the template instance
export const cpaCalculationTemplate = new CPACalculationTemplate();