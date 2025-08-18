/**
 * Revenue Timeline Query Template
 * 
 * Generates time-series revenue data for visualization and trend analysis.
 * Supports various time granularities (daily, weekly, monthly) and partner filtering.
 * Addresses the pain point of creating revenue dashboards and trend visualizations.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for generating revenue timeline data for charts and analytics
 */
export class GetRevenueTimelineTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'get_revenue_timeline',
      'Generate time-series revenue data for visualization, trending, and forecasting with configurable granularity',
      'visualization',
      [
        {
          name: 'start_date',
          type: 'date',
          required: true,
          description: 'Start date for timeline analysis',
          examples: ['2024-01-01', '2024-06-01']
        },
        {
          name: 'end_date',
          type: 'date',
          required: true,
          description: 'End date for timeline analysis',
          examples: ['2024-12-31', '2024-06-30']
        },
        {
          name: 'granularity',
          type: 'string',
          required: false,
          default: 'month',
          description: 'Time granularity for data points',
          examples: ['day', 'week', 'month', 'quarter'],
          validation: {
            pattern: /^(day|week|month|quarter)$/
          }
        },
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Filter timeline for specific partner (leave empty for all)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'partner_type',
          type: 'string',
          required: false,
          description: 'Filter by partner type',
          examples: ['premium', 'standard', 'trial']
        },
        {
          name: 'include_cumulative',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include cumulative revenue in results',
          examples: [true, false]
        },
        {
          name: 'revenue_type',
          type: 'string',
          required: false,
          default: 'all',
          description: 'Type of revenue to include in timeline',
          examples: ['all', 'commission', 'direct', 'recurring'],
          validation: {
            pattern: /^(all|commission|direct|recurring|subscription)$/
          }
        },
        {
          name: 'fill_gaps',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Fill missing time periods with zero values',
          examples: [true, false]
        }
      ],
      {
        painPoint: 'Creating revenue trend visualizations requires complex date aggregation queries that are time-consuming to write and maintain',
        tags: ['timeline', 'revenue', 'visualization', 'trends', 'analytics', 'dashboard']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      start_date, 
      end_date, 
      granularity, 
      partner_id, 
      partner_type,
      include_cumulative,
      revenue_type,
      fill_gaps
    } = params;

    // Determine date format based on granularity
    let dateFormat: string;
    let dateGroup: string;
    switch (granularity) {
      case 'day':
        dateFormat = '%Y-%m-%d';
        dateGroup = 'date(r.date)';
        break;
      case 'week':
        dateFormat = '%Y-W%W';
        dateGroup = 'date(r.date) - duration({days: date(r.date).dayOfWeek - 1})';
        break;
      case 'month':
        dateFormat = '%Y-%m';
        dateGroup = 'date({year: r.date.year, month: r.date.month, day: 1})';
        break;
      case 'quarter':
        dateFormat = '%Y-Q%q';
        dateGroup = 'date({year: r.date.year, month: ((r.date.month - 1) / 3) * 3 + 1, day: 1})';
        break;
      default:
        dateFormat = '%Y-%m';
        dateGroup = 'date({year: r.date.year, month: r.date.month, day: 1})';
    }

    let query = `
MATCH (p:Partner)-[:GENERATES]->(r:Revenue)
WHERE r.date >= date('${this.formatDate(start_date)}')
  AND r.date <= date('${this.formatDate(end_date)}')`;

    // Add partner filters
    if (partner_id) {
      query += `\n  AND p.id = '${this.escapeString(partner_id)}'`;
    }

    if (partner_type) {
      query += `\n  AND p.type = '${this.escapeString(partner_type)}'`;
    }

    // Add revenue type filter
    if (revenue_type !== 'all') {
      query += `\n  AND r.type = '${this.escapeString(revenue_type)}'`;
    }

    query += `
WITH ${dateGroup} as period_date,
     sum(r.amount) as period_revenue,
     count(r) as period_transactions,
     count(distinct p) as active_partners,
     avg(r.amount) as avg_transaction_value,
     min(r.amount) as min_transaction,
     max(r.amount) as max_transaction`;

    if (include_cumulative) {
      query += `,
     collect(r.amount) as all_amounts`;
    }

    query += `
ORDER BY period_date ASC`;

    if (include_cumulative) {
      query += `
WITH period_date, 
     period_revenue, 
     period_transactions,
     active_partners,
     avg_transaction_value,
     min_transaction,
     max_transaction,
     sum(period_revenue) OVER (ORDER BY period_date ROWS UNBOUNDED PRECEDING) as cumulative_revenue,
     sum(period_transactions) OVER (ORDER BY period_date ROWS UNBOUNDED PRECEDING) as cumulative_transactions`;
    }

    query += `
RETURN toString(period_date) as time_period,
       period_date as period_start_date,
       period_revenue,
       period_transactions,
       active_partners,
       round(avg_transaction_value, 2) as avg_transaction_value,
       min_transaction,
       max_transaction`;

    if (include_cumulative) {
      query += `,
       cumulative_revenue,
       cumulative_transactions,
       round(cumulative_revenue / cumulative_transactions, 2) as cumulative_avg_value`;
    }

    // Add growth rate calculation
    query += `,
       CASE 
         WHEN lag(period_revenue) OVER (ORDER BY period_date) IS NULL THEN null
         WHEN lag(period_revenue) OVER (ORDER BY period_date) = 0 THEN 
           CASE WHEN period_revenue > 0 THEN 100.0 ELSE 0.0 END
         ELSE round(((period_revenue - lag(period_revenue) OVER (ORDER BY period_date)) 
                     / lag(period_revenue) OVER (ORDER BY period_date)) * 100, 2)
       END as growth_rate_percent,
       
       // Moving averages (3-period)
       round(avg(period_revenue) OVER (ORDER BY period_date ROWS 2 PRECEDING), 2) as moving_avg_revenue_3period,
       round(avg(period_transactions) OVER (ORDER BY period_date ROWS 2 PRECEDING), 2) as moving_avg_transactions_3period

ORDER BY period_date ASC`;

    return query;
  }
}

// Example usage scenarios
export const revenueTimelineUsage = {
  // Monthly revenue trend for the year
  monthly_trend: {
    name: 'Monthly Revenue Trend',
    description: 'Year-over-year monthly revenue progression with growth rates',
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      granularity: 'month',
      include_cumulative: true,
      fill_gaps: true
    }
  },

  // Daily revenue for specific partner in current month
  partner_daily_analysis: {
    name: 'Partner Daily Revenue Analysis',
    description: 'Daily revenue breakdown for specific partner performance',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      start_date: '2024-06-01',
      end_date: '2024-06-30',
      granularity: 'day',
      include_cumulative: false
    }
  },

  // Weekly commission revenue timeline
  weekly_commission_tracking: {
    name: 'Weekly Commission Tracking',
    description: 'Commission revenue trends on weekly basis',
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      granularity: 'week',
      revenue_type: 'commission',
      include_cumulative: true,
      fill_gaps: true
    }
  },

  // Quarterly view for premium partners
  quarterly_premium_analysis: {
    name: 'Premium Partners Quarterly Analysis',
    description: 'Quarterly revenue trends for premium tier partners',
    parameters: {
      start_date: '2023-01-01',
      end_date: '2024-12-31',
      granularity: 'quarter',
      partner_type: 'premium',
      include_cumulative: true
    }
  }
};

// Create and export the template instance
export const getRevenueTimelineTemplate = new GetRevenueTimelineTemplate();