/**
 * Partner Self-Service Dashboard Query Template
 * 
 * Provides comprehensive dashboard data specifically designed for partners
 * to view their own performance, commissions, customers, and key metrics.
 * Focuses on self-service capabilities and real-time visibility that partners
 * need for their own business management.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for partner self-service dashboard with comprehensive business metrics
 */
export class GetPartnerSelfDashboardTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'get_partner_self_dashboard',
      'Comprehensive partner self-service dashboard showing performance, commissions, customers, and actionable insights',
      'dashboard',
      [
        {
          name: 'partner_id',
          type: 'string',
          required: true,
          description: 'Partner ID for dashboard data (authenticated partner)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'period_type',
          type: 'string',
          required: false,
          default: 'current_month',
          description: 'Time period for dashboard metrics',
          examples: ['current_month', 'last_30_days', 'current_quarter', 'ytd', 'last_12_months'],
          validation: {
            pattern: /^(current_month|last_30_days|current_quarter|ytd|last_12_months|custom)$/
          }
        },
        {
          name: 'custom_start',
          type: 'date',
          required: false,
          description: 'Custom period start date (required if period_type is custom)',
          examples: ['2024-01-01', '2024-06-01']
        },
        {
          name: 'custom_end',
          type: 'date',
          required: false,
          description: 'Custom period end date (required if period_type is custom)',
          examples: ['2024-12-31', '2024-06-30']
        },
        {
          name: 'include_comparison',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include comparison with previous period',
          examples: [true, false]
        },
        {
          name: 'include_goals',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include goal tracking and progress indicators',
          examples: [true, false]
        },
        {
          name: 'include_alerts',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include performance alerts and recommendations',
          examples: [true, false]
        },
        {
          name: 'customer_details',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include detailed customer performance breakdown',
          examples: [true, false]
        }
      ],
      {
        painPoint: 'Partners lack real-time visibility into their performance metrics and need self-service access to their business data',
        tags: ['dashboard', 'partner', 'self-service', 'metrics', 'performance', 'commission']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      partner_id,
      period_type,
      custom_start,
      custom_end,
      include_comparison,
      include_goals,
      include_alerts,
      customer_details
    } = params;

    // Calculate period dates based on period_type
    let periodStart: string;
    let periodEnd: string;
    let comparisonStart: string;
    let comparisonEnd: string;

    const today = new Date();
    
    switch (period_type) {
      case 'current_month':
        periodStart = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`;
        periodEnd = this.formatDate(today);
        const prevMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        comparisonStart = this.formatDate(prevMonth);
        comparisonEnd = new Date(today.getFullYear(), today.getMonth(), 0).toISOString().split('T')[0];
        break;
      case 'last_30_days':
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);
        periodStart = this.formatDate(thirtyDaysAgo);
        periodEnd = this.formatDate(today);
        const sixtyDaysAgo = new Date(today);
        sixtyDaysAgo.setDate(today.getDate() - 60);
        comparisonStart = this.formatDate(sixtyDaysAgo);
        comparisonEnd = this.formatDate(thirtyDaysAgo);
        break;
      case 'current_quarter':
        const quarter = Math.floor(today.getMonth() / 3);
        periodStart = `${today.getFullYear()}-${String(quarter * 3 + 1).padStart(2, '0')}-01`;
        periodEnd = this.formatDate(today);
        const prevQuarter = new Date(today.getFullYear(), (quarter - 1) * 3, 1);
        if (quarter === 0) {
          prevQuarter.setFullYear(today.getFullYear() - 1);
          prevQuarter.setMonth(9);
        }
        comparisonStart = this.formatDate(prevQuarter);
        comparisonEnd = new Date(prevQuarter.getFullYear(), prevQuarter.getMonth() + 3, 0).toISOString().split('T')[0];
        break;
      case 'ytd':
        periodStart = `${today.getFullYear()}-01-01`;
        periodEnd = this.formatDate(today);
        comparisonStart = `${today.getFullYear() - 1}-01-01`;
        comparisonEnd = `${today.getFullYear() - 1}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        break;
      case 'last_12_months':
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        periodStart = this.formatDate(oneYearAgo);
        periodEnd = this.formatDate(today);
        const twoYearsAgo = new Date(today);
        twoYearsAgo.setFullYear(today.getFullYear() - 2);
        comparisonStart = this.formatDate(twoYearsAgo);
        comparisonEnd = this.formatDate(oneYearAgo);
        break;
      case 'custom':
        periodStart = this.formatDate(custom_start);
        periodEnd = this.formatDate(custom_end);
        // For custom periods, comparison is same length ending at start date
        const customDays = Math.floor((new Date(custom_end).getTime() - new Date(custom_start).getTime()) / (1000 * 60 * 60 * 24));
        const compEnd = new Date(custom_start);
        compEnd.setDate(compEnd.getDate() - 1);
        const compStart = new Date(compEnd);
        compStart.setDate(compEnd.getDate() - customDays);
        comparisonStart = this.formatDate(compStart);
        comparisonEnd = this.formatDate(compEnd);
        break;
      default:
        periodStart = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`;
        periodEnd = this.formatDate(today);
        comparisonStart = comparisonEnd = periodStart;
    }

    let query = `
// Partner Dashboard Query - Self-Service Analytics
WITH '${this.escapeString(partner_id)}' as target_partner_id,
     date('${periodStart}') as period_start,
     date('${periodEnd}') as period_end`;

    if (include_comparison) {
      query += `,
     date('${comparisonStart}') as comp_start,
     date('${comparisonEnd}') as comp_end`;
    }

    query += `
// Get partner basic information
MATCH (p:Partner {id: target_partner_id})

// Current period revenue and transactions
OPTIONAL MATCH (p)-[:GENERATES]->(r:Revenue)
WHERE r.date >= period_start AND r.date <= period_end

// Current period commissions
OPTIONAL MATCH (p)-[:EARNS]->(comm:Commission)
WHERE comm.date >= period_start AND comm.date <= period_end

// Current period customers and transactions
OPTIONAL MATCH (p)-[:MANAGES]->(c:Customer)
OPTIONAL MATCH (c)-[:MADE]->(t:Transaction)
WHERE t.date >= period_start AND t.date <= period_end`;

    if (include_comparison) {
      query += `
// Comparison period data
OPTIONAL MATCH (p)-[:GENERATES]->(r_comp:Revenue)
WHERE r_comp.date >= comp_start AND r_comp.date <= comp_end

OPTIONAL MATCH (p)-[:EARNS]->(comm_comp:Commission)
WHERE comm_comp.date >= comp_start AND comm_comp.date <= comp_end

OPTIONAL MATCH (c)-[:MADE]->(t_comp:Transaction)
WHERE t_comp.date >= comp_start AND t_comp.date <= comp_end`;
    }

    if (include_goals) {
      query += `
// Partner goals and targets
OPTIONAL MATCH (p)-[:HAS_GOAL]->(g:Goal)
WHERE g.period_start <= period_end AND g.period_end >= period_start`;
    }

    query += `
// Calculate current period metrics
WITH p,
     // Revenue metrics
     coalesce(sum(r.amount), 0) as total_revenue,
     coalesce(count(distinct r), 0) as revenue_transactions,
     coalesce(avg(r.amount), 0) as avg_revenue_per_transaction,
     
     // Commission metrics
     coalesce(sum(comm.amount), 0) as total_commission,
     coalesce(count(distinct comm), 0) as commission_count,
     
     // Customer and transaction metrics
     coalesce(count(distinct c), 0) as active_customers,
     coalesce(sum(t.amount), 0) as transaction_volume,
     coalesce(count(distinct t), 0) as transaction_count,
     coalesce(avg(t.amount), 0) as avg_transaction_value`;

    if (include_comparison) {
      query += `,
     // Comparison period metrics
     coalesce(sum(r_comp.amount), 0) as comp_revenue,
     coalesce(count(distinct r_comp), 0) as comp_revenue_transactions,
     coalesce(sum(comm_comp.amount), 0) as comp_commission,
     coalesce(count(distinct t_comp), 0) as comp_transactions`;
    }

    if (include_goals) {
      query += `,
     // Goals and targets
     collect(distinct {
       goal_type: g.type,
       target_amount: g.target_amount,
       target_date: g.period_end,
       description: g.description
     }) as goals`;
    }

    query += `
// Calculate derived metrics and growth rates
WITH p, total_revenue, revenue_transactions, avg_revenue_per_transaction,
     total_commission, commission_count, active_customers, 
     transaction_volume, transaction_count, avg_transaction_value`;

    if (include_comparison) {
      query += `,
     comp_revenue, comp_revenue_transactions, comp_commission, comp_transactions,
     
     // Growth calculations
     CASE WHEN comp_revenue > 0 
       THEN round(((total_revenue - comp_revenue) / comp_revenue) * 100, 1)
       ELSE CASE WHEN total_revenue > 0 THEN 100.0 ELSE 0.0 END
     END as revenue_growth_percent,
     
     CASE WHEN comp_commission > 0 
       THEN round(((total_commission - comp_commission) / comp_commission) * 100, 1)
       ELSE CASE WHEN total_commission > 0 THEN 100.0 ELSE 0.0 END
     END as commission_growth_percent,
     
     CASE WHEN comp_transactions > 0 
       THEN round(((transaction_count - comp_transactions) / comp_transactions) * 100, 1)
       ELSE CASE WHEN transaction_count > 0 THEN 100.0 ELSE 0.0 END
     END as transaction_growth_percent`;
    }

    if (include_goals) {
      query += `,
     goals,
     // Goal progress calculations
     [goal IN goals | {
       goal_type: goal.goal_type,
       target_amount: goal.target_amount,
       current_amount: CASE goal.goal_type
         WHEN 'revenue' THEN total_revenue
         WHEN 'commission' THEN total_commission
         WHEN 'customers' THEN active_customers
         WHEN 'transactions' THEN transaction_count
         ELSE 0
       END,
       progress_percent: CASE 
         WHEN goal.target_amount > 0 THEN
           round((CASE goal.goal_type
             WHEN 'revenue' THEN total_revenue
             WHEN 'commission' THEN total_commission
             WHEN 'customers' THEN active_customers
             WHEN 'transactions' THEN transaction_count
             ELSE 0
           END / goal.target_amount) * 100, 1)
         ELSE 0
       END,
       target_date: goal.target_date,
       description: goal.description
     }] as goal_progress`;
    }

    // Performance insights and alerts
    if (include_alerts) {
      query += `,
     // Generate performance alerts
     CASE 
       WHEN total_revenue = 0 THEN ['No revenue in current period']
       ELSE []
     END +
     CASE 
       WHEN active_customers = 0 THEN ['No active customers in period']
       ELSE []
     END +`;
      
      if (include_comparison) {
        query += `
     CASE 
       WHEN comp_revenue > 0 AND ((total_revenue - comp_revenue) / comp_revenue) < -0.1 
       THEN ['Revenue declined by more than 10%']
       ELSE []
     END +`;
      }
      
      query += `
     CASE 
       WHEN avg_transaction_value > 0 AND avg_transaction_value < 50 
       THEN ['Average transaction value is below $50']
       ELSE []
     END as alerts`;
    }

    // Customer details if requested
    if (customer_details) {
      query += `
// Get detailed customer performance
OPTIONAL MATCH (p)-[:MANAGES]->(customer:Customer)
OPTIONAL MATCH (customer)-[:MADE]->(cust_trans:Transaction)
WHERE cust_trans.date >= period_start AND cust_trans.date <= period_end

WITH p, total_revenue, revenue_transactions, total_commission, active_customers,
     transaction_volume, transaction_count, avg_transaction_value`;

      if (include_comparison) {
        query += `, revenue_growth_percent, commission_growth_percent, transaction_growth_percent`;
      }
      
      if (include_goals) {
        query += `, goal_progress`;
      }
      
      if (include_alerts) {
        query += `, alerts`;
      }

      query += `,
     collect(distinct {
       customer_id: customer.id,
       customer_name: customer.name,
       customer_status: customer.status,
       total_spent: coalesce(sum(cust_trans.amount), 0),
       transaction_count: coalesce(count(cust_trans), 0),
       avg_transaction: coalesce(avg(cust_trans.amount), 0),
       last_transaction: max(cust_trans.date)
     }) as customer_details`;
    }

    // Final result assembly
    query += `
RETURN {
  // Partner Information
  partner_id: p.id,
  partner_name: p.name,
  partner_type: p.type,
  partner_status: p.status,
  partner_tier: p.tier,
  
  // Period Information
  period_start: toString(period_start),
  period_end: toString(period_end),
  period_type: '${period_type}',
  
  // Key Metrics
  metrics: {
    total_revenue: round(total_revenue, 2),
    total_commission: round(total_commission, 2),
    commission_rate: CASE WHEN total_revenue > 0 
      THEN round((total_commission / total_revenue) * 100, 2)
      ELSE 0 END,
    active_customers: active_customers,
    transaction_count: transaction_count,
    transaction_volume: round(transaction_volume, 2),
    avg_transaction_value: round(avg_transaction_value, 2),
    avg_revenue_per_transaction: round(avg_revenue_per_transaction, 2),
    revenue_per_customer: CASE WHEN active_customers > 0 
      THEN round(total_revenue / active_customers, 2)
      ELSE 0 END
  }`;

    if (include_comparison) {
      query += `,
  
  // Growth Metrics
  growth: {
    revenue_growth_percent: revenue_growth_percent,
    commission_growth_percent: commission_growth_percent,
    transaction_growth_percent: transaction_growth_percent,
    comparison_period: toString(comp_start) + ' to ' + toString(comp_end)
  }`;
    }

    if (include_goals) {
      query += `,
  
  // Goal Progress
  goals: goal_progress`;
    }

    if (include_alerts) {
      query += `,
  
  // Alerts and Recommendations
  alerts: alerts,
  recommendations: CASE 
    WHEN size(alerts) = 0 THEN ['Performance is on track']
    WHEN total_revenue = 0 THEN ['Focus on customer acquisition and activation']
    WHEN active_customers < 5 THEN ['Expand customer base for stability']
    WHEN avg_transaction_value < 100 THEN ['Work on increasing transaction values']
    ELSE ['Review performance metrics and customer engagement']
  END`;
    }

    if (customer_details) {
      query += `,
  
  // Customer Details
  customers: [c IN customer_details WHERE c.customer_id IS NOT NULL | c]`;
    }

    query += `
} as dashboard_data`;

    return query;
  }
}

// Example usage scenarios
export const partnerSelfDashboardUsage = {
  // Current month dashboard with all features
  full_dashboard: {
    name: 'Complete Partner Dashboard',
    description: 'Full-featured dashboard with all metrics, comparisons, and alerts',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      period_type: 'current_month',
      include_comparison: true,
      include_goals: true,
      include_alerts: true,
      customer_details: true
    }
  },

  // Simple performance overview
  simple_overview: {
    name: 'Simple Performance Overview',
    description: 'Basic dashboard showing key metrics without detailed analysis',
    parameters: {
      partner_id: 'PARTNER_X7Y8Z9W0',
      period_type: 'last_30_days',
      include_comparison: false,
      include_goals: false,
      include_alerts: false,
      customer_details: false
    }
  },

  // Quarterly business review
  quarterly_review: {
    name: 'Quarterly Business Review Dashboard',
    description: 'Comprehensive quarterly dashboard for business reviews',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      period_type: 'current_quarter',
      include_comparison: true,
      include_goals: true,
      include_alerts: true,
      customer_details: true
    }
  },

  // Custom period analysis
  custom_period: {
    name: 'Custom Period Analysis',
    description: 'Dashboard for custom date range analysis',
    parameters: {
      partner_id: 'PARTNER_Y9Z8X7W6',
      period_type: 'custom',
      custom_start: '2024-03-01',
      custom_end: '2024-05-31',
      include_comparison: true,
      include_goals: false,
      include_alerts: true
    }
  }
};

// Create and export the template instance
export const getPartnerSelfDashboardTemplate = new GetPartnerSelfDashboardTemplate();