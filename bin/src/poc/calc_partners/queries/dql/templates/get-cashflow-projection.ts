/**
 * Cashflow Projection Query Template
 * 
 * Calculates future cashflow projections based on historical data, recurring revenues,
 * and scheduled payments. Uses various forecasting methods including trend analysis
 * and seasonal adjustments. Addresses the critical pain point of financial planning.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating future cashflow projections and financial forecasts
 */
export class GetCashflowProjectionTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'get_cashflow_projection',
      'Calculate future cashflow projections using historical data, recurring revenue patterns, and scheduled payments',
      'financial',
      [
        {
          name: 'projection_start',
          type: 'date',
          required: true,
          description: 'Start date for cashflow projection (typically today or start of next month)',
          examples: ['2024-07-01', '2024-08-01']
        },
        {
          name: 'projection_months',
          type: 'number',
          required: false,
          default: 12,
          description: 'Number of months to project forward',
          examples: [3, 6, 12, 24],
          validation: {
            min: 1,
            max: 60
          }
        },
        {
          name: 'historical_months',
          type: 'number',
          required: false,
          default: 12,
          description: 'Number of historical months to analyze for trends',
          examples: [6, 12, 18, 24],
          validation: {
            min: 3,
            max: 36
          }
        },
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Project cashflow for specific partner (leave empty for all)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'confidence_level',
          type: 'string',
          required: false,
          default: 'medium',
          description: 'Projection confidence level affecting growth assumptions',
          examples: ['conservative', 'medium', 'optimistic'],
          validation: {
            pattern: /^(conservative|medium|optimistic)$/
          }
        },
        {
          name: 'include_seasonality',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Apply seasonal adjustments based on historical patterns',
          examples: [true, false]
        },
        {
          name: 'revenue_types',
          type: 'array',
          required: false,
          default: ['all'],
          description: 'Types of revenue to include in projections',
          examples: [['all'], ['recurring', 'commission'], ['direct', 'subscription']]
        },
        {
          name: 'include_scheduled',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include known scheduled payments and contracts',
          examples: [true, false]
        }
      ],
      {
        painPoint: 'Financial planning requires accurate cashflow projections but manual forecasting is time-consuming and error-prone',
        tags: ['cashflow', 'projection', 'forecast', 'financial', 'planning', 'trends']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      projection_start, 
      projection_months, 
      historical_months,
      partner_id,
      confidence_level,
      include_seasonality,
      revenue_types,
      include_scheduled
    } = params;

    // Calculate historical period
    const historicalStart = new Date(projection_start);
    historicalStart.setMonth(historicalStart.getMonth() - historical_months);
    
    // Growth multipliers based on confidence level
    let growthMultiplier: number;
    switch (confidence_level) {
      case 'conservative': growthMultiplier = 0.8; break;
      case 'optimistic': growthMultiplier = 1.2; break;
      default: growthMultiplier = 1.0; break;
    }

    let query = `
// First, gather historical revenue data for trend analysis
WITH date('${this.formatDate(historicalStart)}') as hist_start,
     date('${this.formatDate(projection_start)}') as proj_start,
     ${projection_months} as proj_months,
     ${historical_months} as hist_months,
     ${growthMultiplier} as growth_mult

MATCH (p:Partner)-[:GENERATES]->(r:Revenue)
WHERE r.date >= hist_start 
  AND r.date < proj_start`;

    // Add partner filter if specified
    if (partner_id) {
      query += `\n  AND p.id = '${this.escapeString(partner_id)}'`;
    }

    // Add revenue type filter if not 'all'
    const revTypes = Array.isArray(revenue_types) ? revenue_types : [revenue_types];
    if (!revTypes.includes('all')) {
      const typeFilter = revTypes.map(t => `'${this.escapeString(t)}'`).join(', ');
      query += `\n  AND r.type IN [${typeFilter}]`;
    }

    query += `
// Group historical data by month for trend calculation
WITH hist_start, proj_start, proj_months, hist_months, growth_mult,
     date({year: r.date.year, month: r.date.month, day: 1}) as month_period,
     sum(r.amount) as monthly_revenue,
     count(r) as monthly_transactions,
     p
ORDER BY month_period

// Calculate historical averages and trends
WITH hist_start, proj_start, proj_months, growth_mult,
     collect({
       month: month_period,
       revenue: monthly_revenue,
       transactions: monthly_transactions,
       month_num: (month_period.year - hist_start.year) * 12 + month_period.month - hist_start.month
     }) as historical_data,
     avg(monthly_revenue) as avg_monthly_revenue,
     count(distinct month_period) as actual_months,
     sum(monthly_revenue) as total_historical_revenue

// Calculate trend line using simple linear regression
UNWIND range(0, proj_months - 1) as future_month_offset
WITH hist_start, proj_start, proj_months, growth_mult, historical_data, 
     avg_monthly_revenue, total_historical_revenue,
     future_month_offset,
     date(proj_start) + duration({months: future_month_offset}) as projection_month

// Calculate seasonal adjustment if enabled
WITH *, 
     CASE 
       WHEN ${include_seasonality} THEN
         CASE projection_month.month
           WHEN 1 THEN 0.9   // January - typically slower
           WHEN 2 THEN 0.95  // February
           WHEN 3 THEN 1.1   // March - quarter end boost
           WHEN 4 THEN 1.05  // April
           WHEN 5 THEN 1.0   // May
           WHEN 6 THEN 1.15  // June - mid-year push
           WHEN 7 THEN 0.95  // July - summer slowdown
           WHEN 8 THEN 0.9   // August
           WHEN 9 THEN 1.1   // September - back to business
           WHEN 10 THEN 1.05 // October
           WHEN 11 THEN 1.2  // November - holiday prep
           WHEN 12 THEN 1.25 // December - year-end push
           ELSE 1.0
         END
       ELSE 1.0
     END as seasonal_factor

// Calculate trend-based projection
WITH *,
     // Simple growth trend calculation
     CASE 
       WHEN size(historical_data) > 1 THEN
         (historical_data[-1].revenue - historical_data[0].revenue) / size(historical_data)
       ELSE 0
     END as monthly_trend,
     
     // Base projection using weighted average of recent vs. historical
     (avg_monthly_revenue * 0.7 + 
      CASE WHEN size(historical_data) >= 3 THEN
        (historical_data[-1].revenue + historical_data[-2].revenue + historical_data[-3].revenue) / 3
      ELSE avg_monthly_revenue 
      END * 0.3) as base_projection`;

    // Add scheduled payments if enabled
    if (include_scheduled) {
      query += `
// Include scheduled/recurring payments
OPTIONAL MATCH (p:Partner)-[:HAS_SCHEDULED]->(sp:ScheduledPayment)
WHERE sp.due_date >= proj_start
  AND sp.due_date <= (proj_start + duration({months: proj_months}))
  AND date({year: sp.due_date.year, month: sp.due_date.month, day: 1}) = projection_month`;
    }

    query += `
// Final projection calculation
WITH projection_month,
     future_month_offset,
     round(
       (base_projection + (monthly_trend * future_month_offset)) * 
       growth_mult * 
       seasonal_factor +
       ${include_scheduled ? 'coalesce(sum(sp.amount), 0)' : '0'}
     , 2) as projected_revenue,
     
     // Confidence intervals
     round(
       (base_projection + (monthly_trend * future_month_offset)) * 
       growth_mult * 
       seasonal_factor * 0.8
     , 2) as conservative_projection,
     
     round(
       (base_projection + (monthly_trend * future_month_offset)) * 
       growth_mult * 
       seasonal_factor * 1.2
     , 2) as optimistic_projection,
     
     // Historical context
     avg_monthly_revenue,
     monthly_trend,
     seasonal_factor,
     base_projection${include_scheduled ? ',\n     coalesce(sum(sp.amount), 0) as scheduled_amount' : ''}

RETURN toString(projection_month) as projection_period,
       projection_month as period_start,
       future_month_offset + 1 as month_sequence,
       projected_revenue,
       conservative_projection,
       optimistic_projection,
       round(seasonal_factor, 3) as seasonal_adjustment,
       round(monthly_trend, 2) as trend_component,
       round(base_projection, 2) as base_amount${include_scheduled ? ',\n       scheduled_amount' : ''},
       
       // Cumulative projections
       sum(projected_revenue) OVER (ORDER BY projection_month ROWS UNBOUNDED PRECEDING) as cumulative_projected,
       sum(conservative_projection) OVER (ORDER BY projection_month ROWS UNBOUNDED PRECEDING) as cumulative_conservative,
       sum(optimistic_projection) OVER (ORDER BY projection_month ROWS UNBOUNDED PRECEDING) as cumulative_optimistic,
       
       // Variance from average
       round(((projected_revenue - avg_monthly_revenue) / avg_monthly_revenue) * 100, 1) as variance_from_avg_percent

ORDER BY projection_month ASC`;

    return query;
  }
}

// Example usage scenarios
export const cashflowProjectionUsage = {
  // 12-month conservative projection for all partners
  annual_conservative: {
    name: 'Annual Conservative Cashflow',
    description: '12-month conservative cashflow projection with seasonal adjustments',
    parameters: {
      projection_start: '2024-07-01',
      projection_months: 12,
      historical_months: 12,
      confidence_level: 'conservative',
      include_seasonality: true,
      include_scheduled: true
    }
  },

  // Specific partner 6-month optimistic projection
  partner_growth_forecast: {
    name: 'Partner Growth Forecast',
    description: 'Optimistic 6-month projection for high-performing partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      projection_start: '2024-08-01',
      projection_months: 6,
      historical_months: 18,
      confidence_level: 'optimistic',
      include_seasonality: true
    }
  },

  // Quarterly commission-only projection
  commission_quarterly: {
    name: 'Commission Revenue Quarterly',
    description: 'Quarterly projection focusing on commission revenues',
    parameters: {
      projection_start: '2024-07-01',
      projection_months: 3,
      historical_months: 12,
      revenue_types: ['commission'],
      confidence_level: 'medium',
      include_seasonality: false
    }
  },

  // Long-term strategic planning (24 months)
  strategic_planning: {
    name: 'Long-term Strategic Planning',
    description: '24-month strategic cashflow projection for business planning',
    parameters: {
      projection_start: '2024-07-01',
      projection_months: 24,
      historical_months: 24,
      confidence_level: 'medium',
      include_seasonality: true,
      include_scheduled: true
    }
  }
};

// Create and export the template instance
export const getCashflowProjectionTemplate = new GetCashflowProjectionTemplate();