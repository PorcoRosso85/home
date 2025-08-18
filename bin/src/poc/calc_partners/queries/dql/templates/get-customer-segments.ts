/**
 * Customer Segments Query Template
 * 
 * Analyzes customer segmentation data including value-based segments,
 * behavioral patterns, lifetime value groups, and churn risk categories.
 * Addresses the pain point of understanding customer base composition
 * and targeting strategies.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for analyzing customer segmentation and behavioral patterns
 */
export class GetCustomerSegmentsTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'get_customer_segments',
      'Analyze customer segmentation based on value, behavior, lifecycle stage, and risk profiles for targeted strategies',
      'analytics',
      [
        {
          name: 'analysis_start',
          type: 'date',
          required: true,
          description: 'Start date for customer behavior analysis',
          examples: ['2024-01-01', '2023-01-01']
        },
        {
          name: 'analysis_end',
          type: 'date',
          required: true,
          description: 'End date for customer behavior analysis',
          examples: ['2024-12-31', '2024-06-30']
        },
        {
          name: 'segment_by',
          type: 'string',
          required: false,
          default: 'value',
          description: 'Primary segmentation criteria',
          examples: ['value', 'behavior', 'lifecycle', 'geography', 'partner'],
          validation: {
            pattern: /^(value|behavior|lifecycle|geography|partner|industry)$/
          }
        },
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Analyze segments for specific partner (leave empty for all)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'include_inactive',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include inactive customers in segmentation',
          examples: [true, false]
        },
        {
          name: 'min_transaction_value',
          type: 'decimal',
          required: false,
          default: 0,
          description: 'Minimum transaction value to include customer',
          examples: [0, 100, 500],
          validation: {
            min: 0
          }
        },
        {
          name: 'segment_count',
          type: 'number',
          required: false,
          default: 5,
          description: 'Number of segments to create for value-based segmentation',
          examples: [3, 5, 10],
          validation: {
            min: 2,
            max: 20
          }
        },
        {
          name: 'include_predictions',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include churn risk and value predictions',
          examples: [true, false]
        },
        {
          name: 'detailed_metrics',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include detailed customer metrics per segment',
          examples: [true, false]
        }
      ],
      {
        painPoint: 'Marketing and sales teams need customer segmentation insights but lack easy access to behavioral and value-based customer analysis',
        tags: ['segments', 'customers', 'behavior', 'value', 'targeting', 'analytics']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      analysis_start, 
      analysis_end, 
      segment_by,
      partner_id,
      include_inactive,
      min_transaction_value,
      segment_count,
      include_predictions,
      detailed_metrics
    } = params;

    let query = `
// Gather customer transaction and behavior data
MATCH (c:Customer)
OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
WHERE t.date >= date('${this.formatDate(analysis_start)}')
  AND t.date <= date('${this.formatDate(analysis_end)}')
  AND t.amount >= ${min_transaction_value}
OPTIONAL MATCH (c)<-[:MANAGES]-(p:Partner)`;

    // Add partner filter if specified
    if (partner_id) {
      query += `
WHERE p.id = '${this.escapeString(partner_id)}'`;
    }

    // Add status filter if not including inactive
    if (!include_inactive) {
      const whereClause = partner_id ? ' AND' : ' WHERE';
      query += `${whereClause} c.status = 'active'`;
    }

    query += `
// Calculate customer metrics
WITH c, p,
     coalesce(sum(t.amount), 0) as total_value,
     coalesce(count(t), 0) as transaction_count,
     coalesce(avg(t.amount), 0) as avg_transaction_value,
     coalesce(min(t.date), null) as first_transaction,
     coalesce(max(t.date), null) as last_transaction,
     coalesce(max(t.date), date('${this.formatDate(analysis_start)}')) as latest_activity

// Calculate additional behavioral metrics
WITH c, p, total_value, transaction_count, avg_transaction_value,
     first_transaction, last_transaction, latest_activity,
     
     // Days since first and last transaction
     CASE WHEN first_transaction IS NOT NULL 
       THEN duration.between(date(first_transaction), date()).days
       ELSE null END as days_since_first,
       
     CASE WHEN last_transaction IS NOT NULL 
       THEN duration.between(date(last_transaction), date()).days
       ELSE null END as days_since_last,
       
     // Customer lifecycle stage
     CASE 
       WHEN first_transaction IS NULL THEN 'prospect'
       WHEN days_since_last <= 30 THEN 'active'
       WHEN days_since_last <= 90 THEN 'at_risk'
       WHEN days_since_last <= 180 THEN 'dormant'
       ELSE 'churned'
     END as lifecycle_stage,
     
     // Transaction frequency (transactions per month)
     CASE 
       WHEN first_transaction IS NOT NULL AND last_transaction IS NOT NULL
       THEN CASE WHEN duration.between(date(first_transaction), date(last_transaction)).days > 0
         THEN (transaction_count * 30.0) / duration.between(date(first_transaction), date(last_transaction)).days
         ELSE transaction_count END
       ELSE 0
     END as monthly_frequency`;

    // Add specific segmentation logic based on segment_by parameter
    switch (segment_by) {
      case 'value':
        query += `
// Value-based segmentation using percentiles
WITH c, p, total_value, transaction_count, avg_transaction_value,
     first_transaction, last_transaction, days_since_last, lifecycle_stage, monthly_frequency,
     
     // Calculate percentile ranks for value segmentation
     percentileRank(total_value) as value_percentile
     
WITH *, 
     CASE 
       WHEN value_percentile >= 0.8 THEN 'High Value'
       WHEN value_percentile >= 0.6 THEN 'Medium-High Value'
       WHEN value_percentile >= 0.4 THEN 'Medium Value'
       WHEN value_percentile >= 0.2 THEN 'Low-Medium Value'
       ELSE 'Low Value'
     END as segment_name`;
        break;

      case 'behavior':
        query += `
// Behavioral segmentation based on frequency and recency
WITH c, p, total_value, transaction_count, avg_transaction_value,
     first_transaction, last_transaction, days_since_last, lifecycle_stage, monthly_frequency,
     
     CASE 
       WHEN monthly_frequency >= 4 AND days_since_last <= 30 THEN 'Champions'
       WHEN total_value >= 1000 AND days_since_last <= 60 THEN 'Loyal Customers'
       WHEN monthly_frequency >= 2 AND days_since_last <= 90 THEN 'Potential Loyalists'
       WHEN total_value < 500 AND days_since_last <= 30 THEN 'New Customers'
       WHEN days_since_last BETWEEN 31 AND 90 THEN 'At Risk'
       WHEN days_since_last BETWEEN 91 AND 180 THEN 'Cannot Lose Them'
       WHEN days_since_last > 180 THEN 'Lost Customers'
       ELSE 'Hibernating'
     END as segment_name`;
        break;

      case 'lifecycle':
        query += `
// Lifecycle-based segmentation
WITH c, p, total_value, transaction_count, avg_transaction_value,
     first_transaction, last_transaction, days_since_last, lifecycle_stage, monthly_frequency,
     
     CASE
       WHEN lifecycle_stage = 'prospect' THEN 'Prospects'
       WHEN lifecycle_stage = 'active' AND days_since_first <= 90 THEN 'New Active'
       WHEN lifecycle_stage = 'active' AND days_since_first > 90 THEN 'Established Active'
       WHEN lifecycle_stage = 'at_risk' THEN 'At Risk'
       WHEN lifecycle_stage = 'dormant' THEN 'Dormant'
       ELSE 'Churned'
     END as segment_name`;
        break;

      default:
        query += `
// Default value-based segmentation
WITH c, p, total_value, transaction_count, avg_transaction_value,
     first_transaction, last_transaction, days_since_last, lifecycle_stage, monthly_frequency,
     
     CASE 
       WHEN total_value >= 5000 THEN 'High Value'
       WHEN total_value >= 2000 THEN 'Medium-High Value'
       WHEN total_value >= 500 THEN 'Medium Value'
       WHEN total_value > 0 THEN 'Low Value'
       ELSE 'No Purchases'
     END as segment_name`;
    }

    // Add churn risk prediction if enabled
    if (include_predictions) {
      query += `
// Add churn risk prediction
WITH *, 
     CASE 
       WHEN days_since_last <= 30 THEN 'Low Risk'
       WHEN days_since_last <= 60 THEN 'Medium Risk'
       WHEN days_since_last <= 120 THEN 'High Risk'
       ELSE 'Critical Risk'
     END as churn_risk,
     
     // Predicted next purchase value (simple model)
     CASE 
       WHEN avg_transaction_value > 0 AND monthly_frequency > 0
       THEN round(avg_transaction_value * (1 + (monthly_frequency * 0.1)), 2)
       ELSE 0
     END as predicted_next_value`;
    }

    // Group by segments and calculate summary statistics
    query += `
// Aggregate by segments
WITH segment_name${include_predictions ? ', churn_risk' : ''}, 
     count(c) as customer_count,
     sum(total_value) as segment_total_value,
     avg(total_value) as segment_avg_value,
     sum(transaction_count) as segment_transactions,
     avg(monthly_frequency) as segment_avg_frequency,
     collect({
       customer_id: c.id,
       customer_name: c.name,
       total_value: total_value,
       transaction_count: transaction_count,
       days_since_last: days_since_last,
       lifecycle_stage: lifecycle_stage${include_predictions ? ',\n       churn_risk: churn_risk,\n       predicted_next_value: predicted_next_value' : ''}
     }) as customers`;

    if (detailed_metrics) {
      query += `,
     min(total_value) as segment_min_value,
     max(total_value) as segment_max_value,
     percentileDisc(total_value, 0.5) as segment_median_value,
     stdDev(total_value) as segment_value_stddev`;
    }

    query += `
// Calculate segment percentages and rankings
WITH *, 
     sum(customer_count) OVER () as total_customers,
     sum(segment_total_value) OVER () as total_business_value

RETURN segment_name,
       customer_count,
       round((customer_count * 100.0) / total_customers, 1) as customer_percentage,
       round(segment_total_value, 2) as segment_total_value,
       round((segment_total_value * 100.0) / total_business_value, 1) as value_percentage,
       round(segment_avg_value, 2) as avg_customer_value,
       segment_transactions,
       round(segment_avg_frequency, 2) as avg_monthly_frequency${detailed_metrics ? ',\n       segment_min_value,\n       segment_max_value,\n       round(segment_median_value, 2) as segment_median_value,\n       round(segment_value_stddev, 2) as value_standard_deviation' : ''},
       
       // Value efficiency metrics
       round(segment_total_value / customer_count, 2) as revenue_per_customer,
       round(segment_transactions / customer_count, 1) as transactions_per_customer${detailed_metrics ? ',\n       customers' : ''}

ORDER BY segment_total_value DESC`;

    return query;
  }
}

// Example usage scenarios
export const customerSegmentsUsage = {
  // Value-based segmentation for all customers
  value_segments: {
    name: 'Customer Value Segmentation',
    description: 'Segment all customers by total value with detailed metrics',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      segment_by: 'value',
      include_inactive: false,
      detailed_metrics: true,
      include_predictions: true
    }
  },

  // Behavioral segmentation for specific partner
  partner_behavior_analysis: {
    name: 'Partner Customer Behavior Analysis',
    description: 'Behavioral segmentation for specific partner customers',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      analysis_start: '2024-01-01',
      analysis_end: '2024-06-30',
      segment_by: 'behavior',
      min_transaction_value: 100,
      include_predictions: true
    }
  },

  // Lifecycle analysis with churn focus
  lifecycle_churn_analysis: {
    name: 'Customer Lifecycle & Churn Analysis',
    description: 'Lifecycle-based segments with churn risk assessment',
    parameters: {
      analysis_start: '2023-01-01',
      analysis_end: '2024-12-31',
      segment_by: 'lifecycle',
      include_inactive: true,
      include_predictions: true,
      detailed_metrics: false
    }
  },

  // High-value customer focus
  premium_customer_segments: {
    name: 'Premium Customer Segmentation',
    description: 'Focus on high-value customer segments for VIP treatment',
    parameters: {
      analysis_start: '2024-01-01',
      analysis_end: '2024-12-31',
      segment_by: 'value',
      min_transaction_value: 1000,
      segment_count: 3,
      detailed_metrics: true,
      include_predictions: true
    }
  }
};

// Create and export the template instance
export const getCustomerSegmentsTemplate = new GetCustomerSegmentsTemplate();