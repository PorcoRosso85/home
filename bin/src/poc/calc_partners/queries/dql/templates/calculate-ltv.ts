/**
 * Customer Lifetime Value (LTV) Calculation Template
 * 
 * Calculates customer lifetime value metrics for partner-acquired customers,
 * enabling better understanding of partner quality and long-term value creation.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating customer lifetime value metrics for partner-acquired customers
 */
export class LTVCalculationTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_partner_ltv',
      'Calculate customer lifetime value (LTV) metrics for customers acquired through partner channels, analyzing partner quality and long-term value generation',
      'analytics',
      [
        TemplateHelpers.createParameter(
          'partner_id',
          'string',
          'Partner ID to calculate customer LTV for (optional - if not provided, calculates for all partners)',
          {
            required: false,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('cohort'),
        TemplateHelpers.createParameter(
          'ltv_calculation_method',
          'string',
          'Method to use for LTV calculation',
          {
            required: false,
            default: 'actual',
            examples: ['actual', 'projected', 'predictive']
          }
        ),
        TemplateHelpers.createParameter(
          'projection_months',
          'number',
          'Number of months to project LTV (used with projected/predictive methods)',
          {
            required: false,
            min: 1,
            max: 60,
            default: 24,
            examples: [12, 18, 24, 36]
          }
        ),
        TemplateHelpers.createParameter(
          'churn_rate_assumption',
          'decimal',
          'Monthly churn rate assumption for LTV projections (as decimal, e.g., 0.05 = 5%)',
          {
            required: false,
            min: 0,
            max: 1,
            default: 0.05,
            examples: [0.02, 0.05, 0.08, 0.12]
          }
        ),
        TemplateHelpers.createParameter(
          'include_expansion_revenue',
          'boolean',
          'Include expansion/upsell revenue in LTV calculations',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'customer_status_filter',
          'string',
          'Filter customers by their current status',
          {
            required: false,
            examples: ['active', 'churned', 'paused', 'all']
          }
        ),
        TemplateHelpers.createParameter(
          'min_customer_tenure_days',
          'number',
          'Minimum customer tenure in days to include in LTV analysis',
          {
            required: false,
            min: 1,
            default: 30,
            examples: [30, 90, 180, 365]
          }
        )
      ],
      {
        painPoint: 'SaaS companies need to understand the long-term value of customers acquired through different partners to optimize partner mix and acquisition spend, but calculating accurate LTV across partner channels is complex',
        tags: ['ltv', 'lifetime-value', 'customer-analytics', 'partner-quality', 'retention', 'revenue-prediction']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      partner_id,
      cohort_start,
      cohort_end,
      ltv_calculation_method,
      projection_months,
      churn_rate_assumption,
      include_expansion_revenue,
      customer_status_filter,
      min_customer_tenure_days
    } = params;

    let query = `
// Calculate Partner Customer LTV Analysis
MATCH (partner:Partner)`;

    // Add partner ID filter if provided
    if (partner_id) {
      query += `\nWHERE partner.code = '${this.escapeString(partner_id)}'`;
    }

    query += `

// Find customers acquired by this partner in the cohort period
MATCH (partner)-[:REFERS]->(customer:Partner)
WHERE customer.created_at >= timestamp('${this.formatDateTime(cohort_start)}')
  AND customer.created_at <= timestamp('${this.formatDateTime(cohort_end)}')
  AND duration.inDays(customer.created_at, now()).days >= ${min_customer_tenure_days}`;

    // Add customer status filter if provided
    if (customer_status_filter && customer_status_filter !== 'all') {
      query += `\n  AND customer.status = '${this.escapeString(customer_status_filter)}'`;
    }

    query += `

// Calculate customer transaction history and revenue
MATCH (customer)-[:GENERATES]->(t:Transaction)
WHERE t.status = 'confirmed'

// Separate initial vs expansion revenue if needed
WITH partner, customer, t,
  CASE WHEN t.transaction_date <= date(customer.created_at) + duration({days: 30}) 
    THEN 'initial' 
    ELSE 'expansion' 
  END AS revenue_type

// Calculate actual LTV metrics per customer
WITH partner, customer, 
  SUM(CASE WHEN revenue_type = 'initial' THEN t.amount ELSE 0 END) AS initial_revenue,
  SUM(CASE WHEN revenue_type = 'expansion' AND ${include_expansion_revenue} THEN t.amount ELSE 0 END) AS expansion_revenue,
  SUM(t.amount) AS total_actual_revenue,
  COUNT(t) AS total_transactions,
  MIN(t.transaction_date) AS first_transaction_date,
  MAX(t.transaction_date) AS last_transaction_date,
  duration.inDays(customer.created_at, COALESCE(MAX(t.transaction_date), now())).days AS customer_tenure_days

// Calculate monthly revenue patterns for projections
WITH partner, customer, initial_revenue, expansion_revenue, total_actual_revenue, 
  total_transactions, first_transaction_date, last_transaction_date, customer_tenure_days,
  
  // Monthly revenue rate (for projection)
  CASE WHEN customer_tenure_days > 0 
    THEN total_actual_revenue / (customer_tenure_days / 30.0)
    ELSE 0 
  END AS monthly_revenue_rate,
  
  // Customer status inference
  CASE 
    WHEN last_transaction_date >= date(now()) - duration({days: 60}) THEN 'active'
    WHEN last_transaction_date >= date(now()) - duration({days: 180}) THEN 'at_risk'
    ELSE 'churned'
  END AS inferred_status

// Calculate projected LTV based on method
WITH partner, customer, initial_revenue, expansion_revenue, total_actual_revenue,
  total_transactions, first_transaction_date, last_transaction_date, customer_tenure_days,
  monthly_revenue_rate, inferred_status,
  
  CASE '${ltv_calculation_method}'
    WHEN 'actual' THEN total_actual_revenue
    WHEN 'projected' THEN 
      // Simple projection: current monthly rate * projection months * (1 - churn rate)^months
      monthly_revenue_rate * ${projection_months} * pow((1 - ${churn_rate_assumption}), ${projection_months})
    WHEN 'predictive' THEN 
      // Predictive: blend actual + projected based on tenure
      CASE WHEN customer_tenure_days >= 365 
        THEN total_actual_revenue  // Use actual for mature customers
        ELSE total_actual_revenue + (monthly_revenue_rate * ${projection_months} * pow((1 - ${churn_rate_assumption}), ${projection_months}))
      END
    ELSE total_actual_revenue
  END AS calculated_ltv

// Aggregate by partner
WITH partner,
  COUNT(customer) AS customers_in_cohort,
  AVG(calculated_ltv) AS avg_customer_ltv,
  PERCENTILE_CONT(calculated_ltv, 0.5) AS median_customer_ltv,
  MIN(calculated_ltv) AS min_customer_ltv,
  MAX(calculated_ltv) AS max_customer_ltv,
  SUM(calculated_ltv) AS total_cohort_ltv,
  
  // Revenue breakdown
  AVG(initial_revenue) AS avg_initial_revenue,
  AVG(expansion_revenue) AS avg_expansion_revenue,
  AVG(total_actual_revenue) AS avg_actual_revenue_per_customer,
  
  // Tenure and activity metrics
  AVG(customer_tenure_days) AS avg_customer_tenure_days,
  AVG(total_transactions) AS avg_transactions_per_customer,
  
  // Status distribution
  COUNT(CASE WHEN inferred_status = 'active' THEN 1 END) AS active_customers,
  COUNT(CASE WHEN inferred_status = 'at_risk' THEN 1 END) AS at_risk_customers,
  COUNT(CASE WHEN inferred_status = 'churned' THEN 1 END) AS churned_customers

// Calculate partner-level LTV insights
WITH partner, customers_in_cohort, avg_customer_ltv, median_customer_ltv, 
  min_customer_ltv, max_customer_ltv, total_cohort_ltv,
  avg_initial_revenue, avg_expansion_revenue, avg_actual_revenue_per_customer,
  avg_customer_tenure_days, avg_transactions_per_customer,
  active_customers, at_risk_customers, churned_customers,
  
  // Calculate retention rate
  CASE WHEN customers_in_cohort > 0 
    THEN (toFloat(active_customers + at_risk_customers) / customers_in_cohort) * 100
    ELSE 0 
  END AS retention_rate_percent,
  
  // LTV quality categorization
  CASE 
    WHEN avg_customer_ltv >= 5000 THEN 'High Value'
    WHEN avg_customer_ltv >= 2000 THEN 'Medium Value'  
    WHEN avg_customer_ltv >= 500 THEN 'Standard Value'
    ELSE 'Low Value'
  END AS ltv_quality_tier,
  
  // LTV prediction confidence
  CASE '${ltv_calculation_method}'
    WHEN 'actual' THEN 'High'
    WHEN 'projected' THEN 
      CASE WHEN avg_customer_tenure_days >= 180 THEN 'Medium' ELSE 'Low' END
    WHEN 'predictive' THEN 'Medium'
    ELSE 'Unknown'
  END AS prediction_confidence

RETURN 
  partner.code AS partner_id,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  
  // Customer cohort metrics
  customers_in_cohort AS total_customers_in_cohort,
  active_customers AS currently_active_customers,
  at_risk_customers AS at_risk_customers,
  churned_customers AS churned_customers,
  retention_rate_percent AS cohort_retention_rate,
  
  // LTV calculations
  '${ltv_calculation_method}' AS ltv_calculation_method,
  avg_customer_ltv AS average_customer_ltv,
  median_customer_ltv AS median_customer_ltv,
  min_customer_ltv AS minimum_customer_ltv,
  max_customer_ltv AS maximum_customer_ltv,
  total_cohort_ltv AS total_cohort_value,
  ltv_quality_tier AS partner_ltv_quality,
  prediction_confidence AS ltv_confidence_level,
  
  // Revenue composition
  avg_initial_revenue AS avg_initial_customer_revenue,
  avg_expansion_revenue AS avg_expansion_customer_revenue,
  avg_actual_revenue_per_customer AS avg_realized_revenue_per_customer,
  
  // Engagement metrics
  avg_customer_tenure_days AS avg_customer_tenure_days,
  avg_transactions_per_customer AS avg_transactions_per_customer,
  
  // Efficiency metrics
  CASE WHEN customers_in_cohort > 0 
    THEN total_cohort_ltv / customers_in_cohort 
    ELSE 0 
  END AS ltv_per_acquisition,
  
  '${this.formatDate(cohort_start)}' AS cohort_period_start,
  '${this.formatDate(cohort_end)}' AS cohort_period_end

ORDER BY average_customer_ltv DESC, total_cohort_value DESC`;

    return query;
  }
}

// Example usage scenarios
export const ltvCalculationExamples = {
  // Basic LTV analysis for all partners
  basic: {
    name: 'Quarterly Partner LTV Analysis',
    description: 'Calculate actual LTV for customers acquired by all partners in Q1',
    parameters: {
      cohort_start: '2024-01-01',
      cohort_end: '2024-03-31',
      ltv_calculation_method: 'actual'
    }
  },

  // Projected LTV for a specific partner
  projected: {
    name: 'Specific Partner LTV Projection',
    description: 'Calculate projected 24-month LTV for customers acquired by a specific partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      cohort_start: '2024-01-01',
      cohort_end: '2024-12-31',
      ltv_calculation_method: 'projected',
      projection_months: 24,
      churn_rate_assumption: 0.05,
      include_expansion_revenue: true
    }
  },

  // High-retention partner analysis
  mature_customers: {
    name: 'High-Tenure Customer LTV Analysis',
    description: 'Analyze LTV for customers with at least 6 months tenure from top-tier partners',
    parameters: {
      cohort_start: '2023-01-01',
      cohort_end: '2023-06-30',
      ltv_calculation_method: 'predictive',
      projection_months: 36,
      churn_rate_assumption: 0.03,
      customer_status_filter: 'active',
      min_customer_tenure_days: 180,
      include_expansion_revenue: true
    }
  },

  // Partner quality assessment
  quality_assessment: {
    name: 'Partner Quality Assessment via LTV',
    description: 'Compare partner performance based on customer LTV and retention',
    parameters: {
      cohort_start: '2024-01-01',
      cohort_end: '2024-12-31',
      ltv_calculation_method: 'predictive',
      projection_months: 18,
      churn_rate_assumption: 0.07,
      min_customer_tenure_days: 30,
      include_expansion_revenue: true
    }
  }
};

// Create and export the template instance
export const ltvCalculationTemplate = new LTVCalculationTemplate();