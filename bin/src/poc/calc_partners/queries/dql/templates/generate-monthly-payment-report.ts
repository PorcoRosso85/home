/**
 * Monthly Payment Report Query Template
 * 
 * Generates comprehensive monthly payment reports including partner commissions,
 * payment schedules, outstanding balances, and reconciliation data.
 * Addresses the critical pain point of payment processing automation
 * and financial reconciliation workflows.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Template for generating detailed monthly payment reports with reconciliation data
 */
export class GenerateMonthlyPaymentReportTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'generate_monthly_payment_report',
      'Generate comprehensive monthly payment reports with commission calculations, payment schedules, and reconciliation data',
      'financial',
      [
        {
          name: 'report_month',
          type: 'date',
          required: true,
          description: 'Month for payment report (first day of month)',
          examples: ['2024-06-01', '2024-07-01']
        },
        {
          name: 'partner_id',
          type: 'string',
          required: false,
          description: 'Generate report for specific partner (leave empty for all)',
          examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
        },
        {
          name: 'include_pending',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include pending/unprocessed payments in report',
          examples: [true, false]
        },
        {
          name: 'include_adjustments',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include manual adjustments and corrections',
          examples: [true, false]
        },
        {
          name: 'payment_status',
          type: 'string',
          required: false,
          default: 'all',
          description: 'Filter by payment status',
          examples: ['all', 'pending', 'processed', 'failed', 'cancelled'],
          validation: {
            pattern: /^(all|pending|processed|failed|cancelled|scheduled)$/
          }
        },
        {
          name: 'minimum_amount',
          type: 'decimal',
          required: false,
          default: 0,
          description: 'Minimum payment amount to include in report',
          examples: [0, 50, 100],
          validation: {
            min: 0
          }
        },
        {
          name: 'include_tax_details',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include detailed tax calculations and withholdings',
          examples: [true, false]
        },
        {
          name: 'group_by_tier',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Group results by partner tier for tiered reporting',
          examples: [true, false]
        },
        {
          name: 'include_reconciliation',
          type: 'boolean',
          required: false,
          default: true,
          description: 'Include reconciliation data and variance analysis',
          examples: [true, false]
        },
        {
          name: 'export_format',
          type: 'string',
          required: false,
          default: 'detailed',
          description: 'Level of detail in the report',
          examples: ['summary', 'detailed', 'reconciliation'],
          validation: {
            pattern: /^(summary|detailed|reconciliation)$/
          }
        }
      ],
      {
        painPoint: 'Monthly payment processing requires manual report generation and reconciliation, leading to delays and errors in partner payments',
        tags: ['payments', 'commission', 'reconciliation', 'monthly', 'financial', 'reporting']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      report_month,
      partner_id,
      include_pending,
      include_adjustments,
      payment_status,
      minimum_amount,
      include_tax_details,
      group_by_tier,
      include_reconciliation,
      export_format
    } = params;

    // Calculate month boundaries
    const reportDate = new Date(report_month);
    const monthStart = new Date(reportDate.getFullYear(), reportDate.getMonth(), 1);
    const monthEnd = new Date(reportDate.getFullYear(), reportDate.getMonth() + 1, 0);
    const monthStartStr = this.formatDate(monthStart);
    const monthEndStr = this.formatDate(monthEnd);

    let query = `
// Monthly Payment Report Generation
WITH date('${monthStartStr}') as month_start,
     date('${monthEndStr}') as month_end,
     '${monthStartStr}' as report_period

// Match partners and their payment-related data
MATCH (p:Partner)`;

    // Add partner filter if specified
    if (partner_id) {
      query += `
WHERE p.id = '${this.escapeString(partner_id)}'`;
    }

    query += `
// Get commissions earned in the report month
OPTIONAL MATCH (p)-[:EARNS]->(comm:Commission)
WHERE comm.date >= month_start AND comm.date <= month_end`;

    // Add payment status filter if not 'all'
    if (payment_status !== 'all') {
      query += `
  AND comm.payment_status = '${this.escapeString(payment_status)}'`;
    }

    query += `
// Get scheduled payments for the month
OPTIONAL MATCH (p)-[:HAS_SCHEDULED]->(sp:ScheduledPayment)
WHERE sp.due_date >= month_start AND sp.due_date <= month_end`;

    // Include pending payments if requested
    if (include_pending) {
      query += `
// Get pending payments from previous months
OPTIONAL MATCH (p)-[:EARNS]->(pending_comm:Commission)
WHERE pending_comm.payment_status IN ['pending', 'scheduled']
  AND pending_comm.date < month_start`;
    }

    // Include adjustments if requested
    if (include_adjustments) {
      query += `
// Get manual adjustments for the month
OPTIONAL MATCH (p)-[:HAS]->(adj:PaymentAdjustment)
WHERE adj.adjustment_date >= month_start AND adj.adjustment_date <= month_end`;
    }

    // Include tax details if requested
    if (include_tax_details) {
      query += `
// Get tax withholding information
OPTIONAL MATCH (p)-[:HAS]->(tax:TaxWithholding)
WHERE tax.applicable_month = report_period`;
    }

    query += `
// Calculate payment amounts and details
WITH p,
     // Current month commission earnings
     coalesce(sum(comm.amount), 0) as monthly_commission,
     coalesce(count(comm), 0) as commission_transactions,
     coalesce(avg(comm.amount), 0) as avg_commission,
     
     // Scheduled payments
     coalesce(sum(sp.amount), 0) as scheduled_amount,
     coalesce(count(sp), 0) as scheduled_count,
     
     // Payment status breakdown
     sum(CASE WHEN comm.payment_status = 'processed' THEN comm.amount ELSE 0 END) as processed_amount,
     sum(CASE WHEN comm.payment_status = 'pending' THEN comm.amount ELSE 0 END) as pending_amount,
     sum(CASE WHEN comm.payment_status = 'failed' THEN comm.amount ELSE 0 END) as failed_amount`;

    if (include_pending) {
      query += `,
     // Pending from previous months
     coalesce(sum(pending_comm.amount), 0) as previous_pending`;
    }

    if (include_adjustments) {
      query += `,
     // Manual adjustments
     coalesce(sum(adj.amount), 0) as adjustment_amount,
     coalesce(count(adj), 0) as adjustment_count`;
    }

    if (include_tax_details) {
      query += `,
     // Tax calculations
     coalesce(tax.withholding_rate, 0) as tax_rate,
     coalesce(tax.withholding_amount, 0) as tax_withheld`;
    }

    // Calculate total payment due
    query += `
// Calculate final payment amounts
WITH p, monthly_commission, commission_transactions, avg_commission,
     scheduled_amount, scheduled_count, processed_amount, pending_amount, failed_amount`;

    if (include_pending) {
      query += `, previous_pending`;
    }
    if (include_adjustments) {
      query += `, adjustment_amount, adjustment_count`;
    }
    if (include_tax_details) {
      query += `, tax_rate, tax_withheld`;
    }

    query += `,
     // Total payment calculation
     monthly_commission + scheduled_amount`;
    
    if (include_pending) {
      query += ` + previous_pending`;
    }
    if (include_adjustments) {
      query += ` + adjustment_amount`;
    }
    
    query += ` as gross_payment,
     
     // Net payment after deductions
     (monthly_commission + scheduled_amount`;
    
    if (include_pending) {
      query += ` + previous_pending`;
    }
    if (include_adjustments) {
      query += ` + adjustment_amount`;
    }
    
    query += `)`;
    
    if (include_tax_details) {
      query += ` - tax_withheld`;
    }
    
    query += ` as net_payment`;

    // Filter by minimum amount
    if (minimum_amount > 0) {
      query += `
WHERE gross_payment >= ${minimum_amount}`;
    }

    // Add reconciliation data if requested
    if (include_reconciliation) {
      query += `
// Add reconciliation data
OPTIONAL MATCH (p)-[:HAS]->(last_payment:Payment)
WHERE last_payment.payment_date >= month_start - duration({months: 1})
  AND last_payment.payment_date < month_start
  
WITH *, 
     coalesce(last_payment.amount, 0) as last_month_payment,
     // Calculate variance from expected
     CASE 
       WHEN monthly_commission > 0 THEN
         abs(monthly_commission - coalesce(last_payment.amount, 0))
       ELSE 0 
     END as payment_variance`;
    }

    // Group by tier if requested
    if (group_by_tier) {
      query += `
// Group by partner tier for summary reporting
WITH p.tier as partner_tier,
     collect({
       partner_id: p.id,
       partner_name: p.name,
       partner_status: p.status,
       gross_payment: round(gross_payment, 2),
       net_payment: round(net_payment, 2),
       monthly_commission: round(monthly_commission, 2),
       commission_transactions: commission_transactions,
       processed_amount: round(processed_amount, 2),
       pending_amount: round(pending_amount, 2)`;

      if (include_tax_details) {
        query += `,
       tax_rate: tax_rate,
       tax_withheld: round(tax_withheld, 2)`;
      }

      if (include_reconciliation) {
        query += `,
       payment_variance: round(payment_variance, 2),
       last_month_payment: round(last_month_payment, 2)`;
      }

      query += `
     }) as tier_partners,
     sum(gross_payment) as tier_gross_total,
     sum(net_payment) as tier_net_total,
     count(*) as tier_partner_count`;
    }

    // Build final results based on export format
    if (export_format === 'summary') {
      query += `
// Summary format
RETURN {
  report_info: {
    report_period: report_period,
    generated_date: toString(date()),
    partner_count: ${group_by_tier ? 'sum(tier_partner_count)' : 'count(*)'},
    total_gross_payments: round(${group_by_tier ? 'sum(tier_gross_total)' : 'sum(gross_payment)'}, 2),
    total_net_payments: round(${group_by_tier ? 'sum(tier_net_total)' : 'sum(net_payment)'}, 2)
  },
  ${group_by_tier ? `
  tier_summary: collect({
    tier: partner_tier,
    partner_count: tier_partner_count,
    gross_total: round(tier_gross_total, 2),
    net_total: round(tier_net_total, 2),
    avg_payment: round(tier_gross_total / tier_partner_count, 2)
  })` : `
  partner_summary: collect({
    partner_id: p.id,
    partner_name: p.name,
    net_payment: round(net_payment, 2),
    status: CASE WHEN net_payment >= 100 THEN 'ready_for_payment' ELSE 'below_threshold' END
  })`}
} as payment_report`;
    } else if (export_format === 'reconciliation') {
      query += `
// Reconciliation format
RETURN {
  report_info: {
    report_period: report_period,
    reconciliation_date: toString(date())
  },
  reconciliation_data: collect({
    partner_id: p.id,
    partner_name: p.name,
    current_commission: round(monthly_commission, 2),
    ${include_reconciliation ? `
    last_month_payment: round(last_month_payment, 2),
    variance: round(payment_variance, 2),
    variance_percent: CASE 
      WHEN last_month_payment > 0 
      THEN round((payment_variance / last_month_payment) * 100, 1)
      ELSE null 
    END,` : ''}
    processed_amount: round(processed_amount, 2),
    pending_amount: round(pending_amount, 2),
    failed_amount: round(failed_amount, 2),
    reconciliation_status: CASE
      WHEN pending_amount = 0 AND failed_amount = 0 THEN 'clean'
      WHEN pending_amount > 0 THEN 'pending_items'
      ELSE 'requires_attention'
    END
  })
} as reconciliation_report`;
    } else {
      // Detailed format (default)
      if (group_by_tier) {
        query += `
// Detailed format grouped by tier
RETURN {
  report_info: {
    report_period: report_period,
    generated_date: toString(date()),
    total_tiers: count(*),
    total_partners: sum(tier_partner_count),
    grand_total_gross: round(sum(tier_gross_total), 2),
    grand_total_net: round(sum(tier_net_total), 2)
  },
  tier_details: collect({
    tier: partner_tier,
    partner_count: tier_partner_count,
    tier_totals: {
      gross: round(tier_gross_total, 2),
      net: round(tier_net_total, 2)
    },
    partners: tier_partners
  })
} as detailed_tier_report`;
      } else {
        query += `
// Detailed format individual partners
RETURN {
  report_info: {
    report_period: report_period,
    generated_date: toString(date()),
    partner_count: count(*),
    total_gross_payments: round(sum(gross_payment), 2),
    total_net_payments: round(sum(net_payment), 2)
  },
  payment_details: collect({
    partner_id: p.id,
    partner_name: p.name,
    partner_tier: p.tier,
    partner_status: p.status,
    payment_breakdown: {
      monthly_commission: round(monthly_commission, 2),
      commission_transactions: commission_transactions,
      avg_commission: round(avg_commission, 2),
      scheduled_amount: round(scheduled_amount, 2)`;

        if (include_pending) {
          query += `,
      previous_pending: round(previous_pending, 2)`;
        }

        if (include_adjustments) {
          query += `,
      adjustments: round(adjustment_amount, 2),
      adjustment_count: adjustment_count`;
        }

        query += `
    },
    payment_status: {
      processed: round(processed_amount, 2),
      pending: round(pending_amount, 2),
      failed: round(failed_amount, 2)
    },`;

        if (include_tax_details) {
          query += `
    tax_details: {
      rate: tax_rate,
      withheld: round(tax_withheld, 2)
    },`;
        }

        query += `
    totals: {
      gross_payment: round(gross_payment, 2),
      net_payment: round(net_payment, 2)
    },
    payment_recommendation: CASE
      WHEN net_payment >= 100 THEN 'process_payment'
      WHEN net_payment > 0 THEN 'hold_until_threshold'
      ELSE 'no_payment_due'
    END`;

        if (include_reconciliation) {
          query += `,
    reconciliation: {
      last_month_payment: round(last_month_payment, 2),
      variance: round(payment_variance, 2),
      status: CASE
        WHEN payment_variance <= 10 THEN 'normal'
        WHEN payment_variance <= 50 THEN 'review'
        ELSE 'investigate'
      END
    }`;
        }

        query += `
  })
} as detailed_payment_report`;
      }
    }

    return query;
  }
}

// Example usage scenarios
export const monthlyPaymentReportUsage = {
  // Standard monthly report for all partners
  standard_monthly: {
    name: 'Standard Monthly Payment Report',
    description: 'Complete monthly payment report with all standard features',
    parameters: {
      report_month: '2024-06-01',
      include_pending: true,
      include_adjustments: true,
      payment_status: 'all',
      include_reconciliation: true,
      export_format: 'detailed'
    }
  },

  // Executive summary report
  executive_summary: {
    name: 'Executive Payment Summary',
    description: 'High-level summary for executive reporting',
    parameters: {
      report_month: '2024-06-01',
      group_by_tier: true,
      export_format: 'summary',
      minimum_amount: 100
    }
  },

  // Reconciliation focused report
  reconciliation_report: {
    name: 'Payment Reconciliation Report',
    description: 'Detailed reconciliation analysis for accounting',
    parameters: {
      report_month: '2024-06-01',
      include_pending: true,
      include_adjustments: true,
      include_reconciliation: true,
      export_format: 'reconciliation'
    }
  },

  // Specific partner payment details
  partner_specific: {
    name: 'Individual Partner Payment Report',
    description: 'Detailed payment report for specific partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      report_month: '2024-06-01',
      include_pending: true,
      include_adjustments: true,
      include_tax_details: true,
      include_reconciliation: true,
      export_format: 'detailed'
    }
  }
};

// Create and export the template instance
export const generateMonthlyPaymentReportTemplate = new GenerateMonthlyPaymentReportTemplate();