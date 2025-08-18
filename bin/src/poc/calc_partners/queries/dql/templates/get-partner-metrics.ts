/**
 * Partner Metrics Query Template
 * 
 * Retrieves comprehensive partner performance metrics including revenue,
 * transaction counts, customer acquisition, and key performance indicators.
 * Addresses the pain point of manual metric compilation for partner management.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for retrieving comprehensive partner performance metrics
 */
export class GetPartnerMetricsTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'get_partner_metrics',
      'Retrieve comprehensive partner performance metrics including revenue, transactions, customers, and KPIs',
      'analytics',
      [
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Specific partner ID to analyze (leave empty for all partners)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'metric_period',
          type: 'string',
          required: false,
          default: 'month',
          description: 'Time period for metric calculation',
          examples: ['week', 'month', 'quarter', 'year'],
          validation: {
            pattern: /^(week|month|quarter|year)$/
          }
        },
        {
          name: 'start_date',
          type: 'date',
          required: true,
          description: 'Start date for metric calculation',
          examples: ['2024-01-01', '2024-06-01']
        },
        {
          name: 'end_date',
          type: 'date',
          required: true,
          description: 'End date for metric calculation',
          examples: ['2024-12-31', '2024-06-30']
        },
        {
          name: 'include_inactive',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include inactive partners in results',
          examples: [true, false]
        },
        {
          name: 'min_transactions',
          type: 'number',
          required: false,
          default: 1,
          description: 'Minimum number of transactions required',
          examples: [1, 5, 10],
          validation: {
            min: 0
          }
        }
      ],
      {
        painPoint: 'Partners and account managers need real-time visibility into performance metrics but currently rely on manual report compilation',
        tags: ['metrics', 'partner', 'performance', 'kpi', 'analytics', 'dashboard']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      partner_id, 
      metric_period, 
      start_date, 
      end_date, 
      include_inactive, 
      min_transactions 
    } = params;

    let query = `
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:GENERATES]->(r:Revenue)
WHERE r.date >= date('${this.formatDate(start_date)}')
  AND r.date <= date('${this.formatDate(end_date)}')
OPTIONAL MATCH (p)-[:MANAGES]->(c:Customer)
OPTIONAL MATCH (p)-[:HAS]->(t:Transaction)
WHERE t.date >= date('${this.formatDate(start_date)}')
  AND t.date <= date('${this.formatDate(end_date)}')
OPTIONAL MATCH (p)-[:EARNS]->(commission:Commission)
WHERE commission.date >= date('${this.formatDate(start_date)}')
  AND commission.date <= date('${this.formatDate(end_date)}')`;

    // Add partner ID filter if provided
    if (partner_id) {
      query += `\nWHERE p.id = '${this.escapeString(partner_id)}'`;
    } else {
      // Add status filter if not including inactive
      if (!include_inactive) {
        query += `\nWHERE p.status = 'active'`;
      }
    }

    // Add transaction count filter
    if (min_transactions > 1) {
      query += `\nWITH p, r, c, t, commission, count(t) as transaction_count
WHERE transaction_count >= ${min_transactions}`;
    }

    query += `
WITH p,
     coalesce(sum(r.amount), 0) as total_revenue,
     coalesce(count(distinct r), 0) as revenue_transactions,
     coalesce(count(distinct c), 0) as total_customers,
     coalesce(count(distinct t), 0) as total_transactions,
     coalesce(sum(commission.amount), 0) as total_commission,
     coalesce(avg(r.amount), 0) as avg_revenue_per_transaction,
     coalesce(min(r.date), null) as first_revenue_date,
     coalesce(max(r.date), null) as last_revenue_date,
     p.created_date as partner_since

RETURN p.id as partner_id,
       p.name as partner_name,
       p.type as partner_type,
       p.status as partner_status,
       p.tier as partner_tier,
       partner_since,
       
       // Revenue Metrics
       total_revenue,
       revenue_transactions,
       avg_revenue_per_transaction,
       first_revenue_date,
       last_revenue_date,
       
       // Customer Metrics
       total_customers,
       CASE 
         WHEN total_customers > 0 THEN total_revenue / total_customers
         ELSE 0
       END as revenue_per_customer,
       
       // Transaction Metrics
       total_transactions,
       CASE 
         WHEN total_transactions > 0 THEN total_revenue / total_transactions
         ELSE 0
       END as avg_transaction_value,
       
       // Commission Metrics
       total_commission,
       CASE 
         WHEN total_revenue > 0 THEN (total_commission / total_revenue) * 100
         ELSE 0
       END as commission_rate_percent,
       
       // Performance Indicators
       CASE 
         WHEN partner_since IS NOT NULL 
         THEN duration.between(date(partner_since), date()).days
         ELSE 0
       END as days_as_partner,
       
       CASE 
         WHEN first_revenue_date IS NOT NULL AND last_revenue_date IS NOT NULL
         THEN duration.between(date(first_revenue_date), date(last_revenue_date)).days + 1
         ELSE 0
       END as active_revenue_days,
       
       // Health Score (0-100)
       CASE
         WHEN total_revenue = 0 THEN 0
         WHEN total_revenue >= 50000 AND total_customers >= 10 THEN 100
         WHEN total_revenue >= 25000 AND total_customers >= 5 THEN 80
         WHEN total_revenue >= 10000 AND total_customers >= 3 THEN 60
         WHEN total_revenue >= 5000 AND total_customers >= 1 THEN 40
         ELSE 20
       END as health_score

ORDER BY total_revenue DESC, partner_name ASC`;

    return query;
  }
}

// Example usage scenarios
export const partnerMetricsUsage = {
  // Get metrics for all active partners in current quarter
  quarterly_overview: {
    name: 'Quarterly Partner Overview',
    description: 'Comprehensive metrics for all active partners in current quarter',
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      metric_period: 'quarter',
      include_inactive: false,
      min_transactions: 1
    }
  },

  // Deep dive on specific high-performing partner
  partner_deep_dive: {
    name: 'Individual Partner Deep Dive',
    description: 'Detailed metrics analysis for a specific partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      metric_period: 'month'
    }
  },

  // Focus on active partners with significant transaction volume
  high_volume_analysis: {
    name: 'High Volume Partners Analysis',
    description: 'Metrics for partners with substantial transaction activity',
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      metric_period: 'year',
      min_transactions: 10,
      include_inactive: false
    }
  }
};

// Create and export the template instance
export const getPartnerMetricsTemplate = new GetPartnerMetricsTemplate();