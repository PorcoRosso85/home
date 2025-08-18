/**
 * Churn Rate Calculation Query Template
 * 
 * Calculates customer and partner churn rates using various methodologies
 * including cohort analysis, time-based churn, and predictive churn scoring.
 * Addresses the critical pain point of customer retention analysis and
 * early warning systems for business sustainability.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating comprehensive churn rates and retention analytics
 */
export class CalculateChurnRateTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_churn_rate',
      'Calculate customer and partner churn rates with cohort analysis, trend identification, and predictive scoring',
      'analytics',
      [
        {
          name: 'analysis_period_start',
          type: 'date',
          required: true,
          description: 'Start date for churn analysis period',
          examples: ['2024-01-01', '2023-07-01']
        },
        {
          name: 'analysis_period_end',
          type: 'date',
          required: true,
          description: 'End date for churn analysis period',
          examples: ['2024-12-31', '2024-06-30']
        },
        {
          name: 'churn_definition_days',
          type: 'number',
          required: false,
          default: 90,
          description: 'Number of days of inactivity to consider as churned',
          examples: [30, 60, 90, 180],
          validation: {
            min: 7,
            max: 365
          }
        },
        {
          name: 'entity_type',
          type: 'string',
          required: false,
          default: 'customer',
          description: 'Type of entity to analyze for churn',
          examples: ['customer', 'partner', 'both'],
          validation: {
            pattern: /^(customer|partner|both)$/
          }
        },
        {
          name: 'cohort_type',
          type: 'string',
          required: false,
          default: 'monthly',
          description: 'Cohort grouping for analysis',
          examples: ['monthly', 'quarterly', 'weekly'],
          validation: {
            pattern: /^(weekly|monthly|quarterly)$/
          }
        },
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Analyze churn for specific partner customers (leave empty for all)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'include_reactivation',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Track customers who churned but later reactivated',
          examples: [true, false]
        },
        {
          name: 'segment_by_value',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Segment churn analysis by customer value tiers',
          examples: [true, false]
        },
        {
          name: 'include_predictions',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include churn risk predictions for active entities',
          examples: [true, false]
        },
        {
          name: 'min_transactions',
          type: 'number',
          required: false,
          default: 1,
          description: 'Minimum transactions required to be considered active',
          examples: [1, 2, 5],
          validation: {
            min: 1
          }
        }
      ],
      {
        painPoint: 'Understanding and predicting customer churn is critical but requires complex analysis of activity patterns and cohort behavior',
        tags: ['churn', 'retention', 'cohort', 'analytics', 'prediction', 'lifecycle']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      analysis_period_start,
      analysis_period_end,
      churn_definition_days,
      entity_type,
      cohort_type,
      partner_id,
      include_reactivation,
      segment_by_value,
      include_predictions,
      min_transactions
    } = params;

    // Determine cohort grouping format
    let cohortDateFormat: string;
    let cohortGroup: string;
    switch (cohort_type) {
      case 'weekly':
        cohortDateFormat = '%Y-W%W';
        cohortGroup = 'date(first_activity) - duration({days: date(first_activity).dayOfWeek - 1})';
        break;
      case 'quarterly':
        cohortDateFormat = '%Y-Q%q';
        cohortGroup = 'date({year: first_activity.year, month: ((first_activity.month - 1) / 3) * 3 + 1, day: 1})';
        break;
      default: // monthly
        cohortDateFormat = '%Y-%m';
        cohortGroup = 'date({year: first_activity.year, month: first_activity.month, day: 1})';
    }

    let query = `
// Churn Rate Analysis - Multi-entity Support
WITH date('${this.formatDate(analysis_period_start)}') as analysis_start,
     date('${this.formatDate(analysis_period_end)}') as analysis_end,
     ${churn_definition_days} as churn_days,
     date() as today`;

    // Build entity matching based on type
    if (entity_type === 'customer' || entity_type === 'both') {
      query += `
// Analyze customer churn
MATCH (c:Customer)
OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
WHERE t.date >= analysis_start - duration({days: 365})  // Look back 1 year for context`;

      if (partner_id) {
        query += `
OPTIONAL MATCH (c)<-[:MANAGES]-(p:Partner {id: '${this.escapeString(partner_id)}'})`;
      }

      query += `
WITH c, 
     coalesce(min(t.date), c.created_date) as first_activity,
     coalesce(max(t.date), c.created_date) as last_activity,
     coalesce(count(t), 0) as total_transactions,
     coalesce(sum(t.amount), 0) as total_value`;

      if (partner_id) {
        query += `
WHERE p IS NOT NULL`;
      }

      query += `
  AND total_transactions >= ${min_transactions}
  AND first_activity >= analysis_start
  AND first_activity <= analysis_end`;
    }

    if (entity_type === 'partner' || entity_type === 'both') {
      if (entity_type === 'both') {
        query += `
UNION ALL

// Analyze partner churn`;
      }
      
      query += `
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:GENERATES]->(r:Revenue)
WHERE r.date >= analysis_start - duration({days: 365})  // Look back 1 year for context

WITH p as c,  // Normalize variable name
     coalesce(min(r.date), p.created_date) as first_activity,
     coalesce(max(r.date), p.created_date) as last_activity,
     coalesce(count(r), 0) as total_transactions,
     coalesce(sum(r.amount), 0) as total_value
WHERE total_transactions >= ${min_transactions}
  AND first_activity >= analysis_start
  AND first_activity <= analysis_end`;
    }

    query += `
// Calculate cohorts and churn status
WITH c, first_activity, last_activity, total_transactions, total_value,
     ${cohortGroup} as cohort_period,
     duration.between(date(last_activity), today).days as days_since_last_activity,
     
     // Determine current status
     CASE 
       WHEN duration.between(date(last_activity), today).days > churn_days THEN 'churned'
       WHEN duration.between(date(last_activity), today).days > churn_days / 2 THEN 'at_risk'
       ELSE 'active'
     END as current_status,
     
     // Value segment if requested
     ${segment_by_value ? `
     CASE 
       WHEN total_value >= 5000 THEN 'high_value'
       WHEN total_value >= 1000 THEN 'medium_value'
       WHEN total_value > 0 THEN 'low_value'
       ELSE 'no_value'
     END as value_segment,` : 'null as value_segment,'}
     
     '${entity_type}' as entity_type`;

    // Add reactivation tracking if enabled
    if (include_reactivation) {
      query += `
// Track reactivation patterns
OPTIONAL MATCH (c)-[:MADE]->(reactivation_trans:Transaction)
WHERE reactivation_trans.date > last_activity + duration({days: churn_days})
  AND reactivation_trans.date <= today

WITH *, 
     CASE 
       WHEN reactivation_trans IS NOT NULL THEN 'reactivated'
       ELSE current_status
     END as final_status,
     min(reactivation_trans.date) as reactivation_date`;
    } else {
      query += `
WITH *, current_status as final_status, null as reactivation_date`;
    }

    // Cohort analysis calculations
    query += `
// Cohort analysis and churn rate calculations
WITH cohort_period,
     ${segment_by_value ? 'value_segment,' : ''}
     count(*) as cohort_size,
     sum(CASE WHEN final_status = 'churned' THEN 1 ELSE 0 END) as churned_count,
     sum(CASE WHEN final_status = 'active' THEN 1 ELSE 0 END) as active_count,
     sum(CASE WHEN final_status = 'at_risk' THEN 1 ELSE 0 END) as at_risk_count,
     ${include_reactivation ? 'sum(CASE WHEN final_status = "reactivated" THEN 1 ELSE 0 END) as reactivated_count,' : ''}
     avg(total_value) as avg_cohort_value,
     avg(total_transactions) as avg_cohort_transactions,
     entity_type

// Calculate rates and metrics
WITH *,
     round((churned_count * 100.0) / cohort_size, 2) as churn_rate_percent,
     round((active_count * 100.0) / cohort_size, 2) as retention_rate_percent,
     round((at_risk_count * 100.0) / cohort_size, 2) as at_risk_rate_percent,
     ${include_reactivation ? 'round((reactivated_count * 100.0) / churned_count, 2) as reactivation_rate_percent,' : ''}
     
     // Customer Lifetime Value estimation for churned vs retained
     CASE WHEN active_count > 0 
       THEN round(avg_cohort_value * (active_count / cohort_size), 2)
       ELSE 0 
     END as retained_value_impact`;

    // Add predictive scoring if enabled
    if (include_predictions) {
      query += `
// Add churn prediction scores for active entities
OPTIONAL MATCH (active_entity)
WHERE active_entity IN [c IN collect(c) WHERE final_status = 'active']
OPTIONAL MATCH (active_entity)-[:MADE|GENERATES]->(recent_activity)
WHERE recent_activity.date >= today - duration({days: 30})

WITH *,
     // Simple churn risk scoring (0-100, higher = more likely to churn)
     collect(DISTINCT {
       entity_id: active_entity.id,
       risk_score: CASE
         WHEN count(recent_activity) = 0 THEN 85  // No recent activity
         WHEN count(recent_activity) = 1 THEN 60  // Low activity
         WHEN count(recent_activity) <= 3 THEN 40  // Medium activity
         WHEN avg(recent_activity.amount) < avg_cohort_value * 0.5 THEN 50  // Declining value
         ELSE 20  // Good activity
       END,
       last_activity_days: duration.between(max(recent_activity.date), today).days,
       monthly_trend: CASE 
         WHEN count(recent_activity) > 0 THEN 'stable'
         ELSE 'declining'
       END
     }) as churn_predictions`;
    }

    query += `
// Final results aggregation
RETURN {
  analysis_period: {
    start: toString(analysis_start),
    end: toString(analysis_end),
    cohort_type: '${cohort_type}',
    churn_definition_days: churn_days
  },
  
  cohort_analysis: collect({
    cohort_period: toString(cohort_period),
    ${segment_by_value ? 'value_segment: value_segment,' : ''}
    entity_type: entity_type,
    cohort_size: cohort_size,
    
    // Status distribution
    active_count: active_count,
    churned_count: churned_count,
    at_risk_count: at_risk_count,
    ${include_reactivation ? 'reactivated_count: reactivated_count,' : ''}
    
    // Rates
    churn_rate_percent: churn_rate_percent,
    retention_rate_percent: retention_rate_percent,
    at_risk_rate_percent: at_risk_rate_percent,
    ${include_reactivation ? 'reactivation_rate_percent: reactivation_rate_percent,' : ''}
    
    // Value metrics
    avg_cohort_value: round(avg_cohort_value, 2),
    avg_cohort_transactions: round(avg_cohort_transactions, 1),
    retained_value_impact: retained_value_impact
  }),
  
  // Overall summary
  summary: {
    total_entities_analyzed: sum(cohort_size),
    overall_churn_rate: round((sum(churned_count) * 100.0) / sum(cohort_size), 2),
    overall_retention_rate: round((sum(active_count) * 100.0) / sum(cohort_size), 2),
    total_value_at_risk: sum(retained_value_impact),
    ${include_reactivation ? 'total_reactivated: sum(reactivated_count),' : ''}
    analysis_date: toString(today)
  }`;

    if (include_predictions) {
      query += `,
  
  // Churn predictions for active entities
  predictions: {
    high_risk_entities: [pred IN flatten(collect(churn_predictions)) WHERE pred.risk_score >= 70],
    medium_risk_entities: [pred IN flatten(collect(churn_predictions)) WHERE pred.risk_score >= 40 AND pred.risk_score < 70],
    low_risk_entities: [pred IN flatten(collect(churn_predictions)) WHERE pred.risk_score < 40]
  }`;
    }

    query += `
} as churn_analysis`;

    return query;
  }
}

// Example usage scenarios
export const churnRateUsage = {
  // Comprehensive customer churn analysis
  customer_churn_analysis: {
    name: 'Customer Churn Analysis',
    description: 'Complete customer churn analysis with cohorts and predictions',
    parameters: {
      analysis_period_start: '2024-01-01',
      analysis_period_end: '2024-06-30',
      churn_definition_days: 90,
      entity_type: 'customer',
      cohort_type: 'monthly',
      include_reactivation: true,
      segment_by_value: true,
      include_predictions: true
    }
  },

  // Partner retention analysis
  partner_retention: {
    name: 'Partner Retention Analysis',
    description: 'Analyze partner churn patterns and retention rates',
    parameters: {
      analysis_period_start: '2023-01-01',
      analysis_period_end: '2024-12-31',
      churn_definition_days: 180,  // Longer period for partners
      entity_type: 'partner',
      cohort_type: 'quarterly',
      include_reactivation: false,
      segment_by_value: false,
      include_predictions: true
    }
  },

  // High-value customer focus
  high_value_churn_focus: {
    name: 'High-Value Customer Churn',
    description: 'Focus on churn patterns among high-value customers',
    parameters: {
      analysis_period_start: '2024-01-01',
      analysis_period_end: '2024-12-31',
      churn_definition_days: 60,  // Shorter period for high-value
      entity_type: 'customer',
      cohort_type: 'monthly',
      segment_by_value: true,
      min_transactions: 3,  // More engaged customers
      include_predictions: true
    }
  },

  // Partner-specific customer churn
  partner_customer_churn: {
    name: 'Partner-Specific Customer Churn',
    description: 'Analyze churn rates for customers of a specific partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      analysis_period_start: '2024-01-01',
      analysis_period_end: '2024-12-31',
      churn_definition_days: 90,
      entity_type: 'customer',
      cohort_type: 'monthly',
      include_reactivation: true,
      include_predictions: true
    }
  }
};

// Create and export the template instance
export const calculateChurnRateTemplate = new CalculateChurnRateTemplate();