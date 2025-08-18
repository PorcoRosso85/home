/**
 * Revenue Share Calculation Template
 * 
 * Calculates revenue sharing between partners in referral networks or joint ventures.
 * Supports hierarchical revenue distribution and multi-level partner relationships.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating revenue sharing between partners based on referral relationships
 */
export class RevenueShareTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_revenue_share',
      'Calculate revenue sharing distribution across partner networks based on referral relationships and contribution levels',
      'revenue',
      [
        TemplateHelpers.createParameter(
          'primary_partner_id',
          'string',
          'Primary partner ID (revenue originator)',
          {
            required: true,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('revenue'),
        TemplateHelpers.createParameter(
          'max_referral_depth',
          'number',
          'Maximum depth of referral chain to consider for sharing',
          {
            required: false,
            min: 1,
            max: 5,
            default: 3,
            examples: [2, 3, 4]
          }
        ),
        TemplateHelpers.createParameter(
          'share_percentage_l1',
          'decimal',
          'Revenue share percentage for level 1 referrers (direct referrers)',
          {
            required: false,
            min: 0,
            max: 0.5,
            default: 0.15,
            examples: [0.10, 0.15, 0.20]
          }
        ),
        TemplateHelpers.createParameter(
          'share_percentage_l2',
          'decimal',
          'Revenue share percentage for level 2 referrers',
          {
            required: false,
            min: 0,
            max: 0.3,
            default: 0.08,
            examples: [0.05, 0.08, 0.10]
          }
        ),
        TemplateHelpers.createParameter(
          'share_percentage_l3',
          'decimal',
          'Revenue share percentage for level 3+ referrers',
          {
            required: false,
            min: 0,
            max: 0.2,
            default: 0.04,
            examples: [0.03, 0.04, 0.05]
          }
        ),
        TemplateHelpers.createParameter(
          'min_revenue_threshold',
          'decimal',
          'Minimum revenue amount to qualify for sharing',
          {
            required: false,
            min: 0,
            default: 100,
            examples: [50, 100, 500]
          }
        )
      ],
      {
        painPoint: 'SaaS companies with multi-level partner programs struggle to fairly distribute revenue shares across referral networks, leading to disputes and manual calculation errors',
        tags: ['revenue', 'sharing', 'referral', 'network', 'mlm', 'distribution']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      primary_partner_id,
      revenue_start,
      revenue_end,
      max_referral_depth,
      share_percentage_l1,
      share_percentage_l2,
      share_percentage_l3,
      min_revenue_threshold
    } = params;

    let query = `
// Calculate Revenue Share Distribution
MATCH (primary:Partner {code: '${this.escapeString(primary_partner_id)}'})-[:GENERATES]->(t:Transaction)
WHERE t.transaction_date >= date('${this.formatDate(revenue_start)}')
  AND t.transaction_date <= date('${this.formatDate(revenue_end)}')
  AND t.status = 'confirmed'
  AND t.amount >= ${min_revenue_threshold}

// Calculate primary partner's base revenue
WITH primary, SUM(t.amount) AS total_revenue, COUNT(t) AS transaction_count

// Find referral chain up to max depth
OPTIONAL MATCH (primary)<-[ref:REFERS*1..${max_referral_depth}]-(referrer:Partner)
WHERE ALL(r IN ref WHERE r.status = 'active')

// Calculate referral depth and sharing rates
WITH primary, total_revenue, transaction_count, referrer,
  CASE 
    WHEN referrer IS NULL THEN 0
    ELSE LENGTH([(primary)<-[:REFERS*]-(referrer:Partner) | referrer])
  END AS referral_depth

// Apply sharing percentages by level
WITH primary, total_revenue, transaction_count, referrer, referral_depth,
  CASE referral_depth
    WHEN 1 THEN ${share_percentage_l1}
    WHEN 2 THEN ${share_percentage_l2}
    WHEN 3 THEN ${share_percentage_l3}
    ELSE ${share_percentage_l3} * 0.5  // Diminishing returns for deeper levels
  END AS share_rate

// Calculate individual shares
WITH primary, total_revenue, transaction_count, 
  COLLECT({
    partner: referrer,
    depth: referral_depth,
    share_rate: share_rate,
    share_amount: total_revenue * share_rate
  }) AS referrer_shares

// Calculate total shared amount and primary partner's remaining share
WITH primary, total_revenue, transaction_count, referrer_shares,
  REDUCE(total_shared = 0.0, share IN referrer_shares | 
    total_shared + CASE WHEN share.partner IS NOT NULL THEN share.share_amount ELSE 0 END
  ) AS total_shared_amount

WITH primary, total_revenue, transaction_count, referrer_shares, total_shared_amount,
  total_revenue - total_shared_amount AS primary_net_revenue

// Return revenue distribution breakdown
UNWIND CASE 
  WHEN SIZE(referrer_shares) = 0 OR referrer_shares[0].partner IS NULL 
  THEN [null] 
  ELSE referrer_shares 
END AS share

RETURN 
  primary.code AS primary_partner_id,
  primary.name AS primary_partner_name,
  total_revenue AS gross_revenue,
  transaction_count AS qualifying_transactions,
  primary_net_revenue AS primary_partner_share,
  (primary_net_revenue / total_revenue * 100) AS primary_share_percentage,
  
  // Referrer information (null for primary partner row)
  CASE WHEN share IS NOT null AND share.partner IS NOT NULL
    THEN share.partner.code 
    ELSE null 
  END AS referrer_partner_id,
  
  CASE WHEN share IS NOT null AND share.partner IS NOT NULL
    THEN share.partner.name 
    ELSE null 
  END AS referrer_partner_name,
  
  CASE WHEN share IS NOT null AND share.partner IS NOT NULL
    THEN share.depth 
    ELSE null 
  END AS referral_depth,
  
  CASE WHEN share IS NOT null AND share.partner IS NOT NULL
    THEN share.share_amount 
    ELSE null 
  END AS referrer_share_amount,
  
  CASE WHEN share IS NOT null AND share.partner IS NOT NULL
    THEN (share.share_rate * 100) 
    ELSE null 
  END AS referrer_share_percentage,

  total_shared_amount AS total_distributed_amount,
  (total_shared_amount / total_revenue * 100) AS total_shared_percentage,
  '${this.formatDate(revenue_start)}' AS calculation_period_start,
  '${this.formatDate(revenue_end)}' AS calculation_period_end

ORDER BY 
  CASE WHEN referrer_partner_id IS NULL THEN 0 ELSE 1 END,  // Primary partner first
  referral_depth ASC,
  referrer_share_amount DESC`;

    return query;
  }
}

// Example usage scenarios
export const revenueShareExamples = {
  // Basic revenue sharing with default settings
  basic: {
    name: 'Basic Revenue Share Distribution',
    description: 'Calculate revenue sharing for a partner with standard percentages',
    parameters: {
      primary_partner_id: 'PARTNER_A1B2C3D4',
      revenue_start: '2024-01-01',
      revenue_end: '2024-01-31'
    }
  },

  // Custom sharing rates for high-value partnerships
  custom_rates: {
    name: 'High-Value Partnership Revenue Share',
    description: 'Custom revenue sharing rates for premium partnership tiers',
    parameters: {
      primary_partner_id: 'PARTNER_X7Y8Z9W0',
      revenue_start: '2024-01-01',
      revenue_end: '2024-12-31',
      max_referral_depth: 4,
      share_percentage_l1: 0.20,
      share_percentage_l2: 0.12,
      share_percentage_l3: 0.06,
      min_revenue_threshold: 500
    }
  },

  // Conservative sharing for new programs
  conservative: {
    name: 'Conservative Revenue Sharing Model',
    description: 'Lower sharing rates for new or experimental partner programs',
    parameters: {
      primary_partner_id: 'PARTNER_B5C6D7E8',
      revenue_start: '2024-01-01',
      revenue_end: '2024-12-31',
      max_referral_depth: 2,
      share_percentage_l1: 0.10,
      share_percentage_l2: 0.05,
      share_percentage_l3: 0.02,
      min_revenue_threshold: 200
    }
  }
};

// Create and export the template instance
export const revenueShareTemplate = new RevenueShareTemplate();