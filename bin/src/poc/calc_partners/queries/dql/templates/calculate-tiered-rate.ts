/**
 * Tiered Rate Calculation Template
 * 
 * Calculates tiered commission rates based on performance thresholds and volume tiers.
 * Supports progressive rate structures where rates increase with higher performance levels.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating tiered commission rates based on partner performance thresholds
 */
export class TieredRateTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_tiered_rate',
      'Calculate progressive commission rates for partners based on performance thresholds and volume tiers within a specified period',
      'commission',
      [
        TemplateHelpers.createParameter(
          'partner_id',
          'string',
          'Partner ID to calculate tiered rates for (optional - if not provided, calculates for all partners)',
          {
            required: false,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('performance'),
        TemplateHelpers.createParameter(
          'tier_metric',
          'string',
          'Metric to use for tier calculation',
          {
            required: false,
            default: 'transaction_amount',
            examples: ['transaction_amount', 'transaction_count', 'monthly_revenue', 'customer_count']
          }
        ),
        TemplateHelpers.createParameter(
          'reward_rule_name',
          'string',
          'Specific reward rule to apply (optional - if not provided, uses all applicable tiered rules)',
          {
            required: false,
            examples: ['Volume Bonus Tier', 'Performance Commission', 'Elite Partner Rates']
          }
        ),
        TemplateHelpers.createParameter(
          'include_bonuses',
          'boolean',
          'Whether to include tier-specific bonuses in calculations',
          {
            required: false,
            default: true,
            examples: [true, false]
          }
        ),
        TemplateHelpers.createParameter(
          'partner_tier_filter',
          'string',
          'Filter partners by their current tier level',
          {
            required: false,
            examples: ['bronze', 'silver', 'gold', 'platinum', 'elite']
          }
        )
      ],
      {
        painPoint: 'SaaS companies need sophisticated tiered commission structures to incentivize partner growth, but calculating progressive rates across multiple tiers and performance metrics is complex and error-prone',
        tags: ['tiered', 'commission', 'progressive', 'threshold', 'performance', 'volume']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      partner_id,
      performance_start,
      performance_end,
      tier_metric,
      reward_rule_name,
      include_bonuses,
      partner_tier_filter
    } = params;

    let query = `
// Calculate Tiered Commission Rates
MATCH (p:Partner)-[:APPLIES_RULE]->(rr:RewardRule {type: 'tiered'})
MATCH (p)-[:GENERATES]->(t:Transaction)
WHERE t.transaction_date >= date('${this.formatDate(performance_start)}')
  AND t.transaction_date <= date('${this.formatDate(performance_end)}')
  AND t.status = 'confirmed'`;

    // Add partner ID filter if provided
    if (partner_id) {
      query += `\n  AND p.code = '${this.escapeString(partner_id)}'`;
    }

    // Add reward rule filter if provided
    if (reward_rule_name) {
      query += `\n  AND rr.name = '${this.escapeString(reward_rule_name)}'`;
    }

    // Add partner tier filter if provided
    if (partner_tier_filter) {
      query += `\n  AND p.tier = '${this.escapeString(partner_tier_filter)}'`;
    }

    query += `

// Calculate performance metrics for tier determination
WITH p, rr, t,
  CASE '${tier_metric}'
    WHEN 'transaction_amount' THEN SUM(t.amount)
    WHEN 'transaction_count' THEN toFloat(COUNT(t))
    WHEN 'monthly_revenue' THEN SUM(t.amount) / 
      (DURATION.BETWEEN(date('${this.formatDate(performance_start)}'), date('${this.formatDate(performance_end)}')).months + 1)
    WHEN 'customer_count' THEN toFloat(COUNT(DISTINCT t.partner_id))
    ELSE SUM(t.amount)
  END AS performance_metric

// Find applicable thresholds for this performance level
MATCH (rr)-[:HAS_THRESHOLD]->(th:Threshold)
WHERE th.metric = '${tier_metric}'
  AND performance_metric >= th.min_value
  AND (th.max_value IS NULL OR performance_metric <= th.max_value)

// Get the highest applicable tier (based on sequence order)
WITH p, rr, performance_metric, th, 
  COLLECT(th) AS applicable_thresholds
ORDER BY th.sequence DESC
LIMIT 1

WITH p, rr, performance_metric, th,
  th.rate AS tier_rate,
  CASE WHEN ${include_bonuses} THEN COALESCE(th.bonus, 0) ELSE 0 END AS tier_bonus

// Calculate total earnings from all transactions at the tier rate
MATCH (p)-[:GENERATES]->(t2:Transaction)
WHERE t2.transaction_date >= date('${this.formatDate(performance_start)}')
  AND t2.transaction_date <= date('${this.formatDate(performance_end)}')
  AND t2.status = 'confirmed'

WITH p, rr, performance_metric, th, tier_rate, tier_bonus,
  SUM(t2.amount) AS total_transaction_value,
  COUNT(t2) AS total_transactions

// Calculate tiered commission
WITH p, rr, performance_metric, th, tier_rate, tier_bonus,
  total_transaction_value, total_transactions,
  (total_transaction_value * tier_rate) + tier_bonus AS total_commission

// Get tier information for display
WITH p, rr, performance_metric, th, tier_rate, tier_bonus,
  total_transaction_value, total_transactions, total_commission,
  CASE 
    WHEN th.max_value IS NULL THEN 'Unlimited'
    ELSE toString(th.max_value)
  END AS tier_max_display

RETURN 
  p.code AS partner_id,
  p.name AS partner_name,
  p.tier AS current_partner_tier,
  rr.name AS reward_rule_name,
  '${tier_metric}' AS tier_metric_used,
  performance_metric AS partner_performance_value,
  
  // Tier information
  th.sequence AS tier_level,
  th.min_value AS tier_min_threshold,
  tier_max_display AS tier_max_threshold,
  (tier_rate * 100) AS tier_rate_percentage,
  tier_bonus AS tier_bonus_amount,
  
  // Transaction and commission details
  total_transactions AS qualifying_transactions,
  total_transaction_value AS total_qualifying_value,
  total_commission AS calculated_commission,
  (total_commission / total_transaction_value * 100) AS effective_commission_rate,
  
  // Performance analysis
  CASE 
    WHEN performance_metric >= (th.min_value * 1.2) THEN 'Exceeding Tier'
    WHEN performance_metric >= (th.min_value * 1.1) THEN 'Strong Performance'  
    ELSE 'Meeting Tier'
  END AS performance_status,
  
  '${this.formatDate(performance_start)}' AS calculation_period_start,
  '${this.formatDate(performance_end)}' AS calculation_period_end

ORDER BY 
  partner_id ASC,
  tier_level DESC,
  total_commission DESC`;

    return query;
  }
}

// Example usage scenarios
export const tieredRateExamples = {
  // Basic tiered rate calculation for a specific partner
  basic: {
    name: 'Partner Tiered Rate Analysis',
    description: 'Calculate tiered commission rates for a specific partner',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      performance_start: '2024-01-01',
      performance_end: '2024-01-31'
    }
  },

  // All partners with volume-based tiers
  volume_based: {
    name: 'Volume-Based Tier Calculation',
    description: 'Calculate all partners tiered rates based on transaction volume',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-12-31',
      tier_metric: 'transaction_amount',
      include_bonuses: true
    }
  },

  // Elite tier partners only with customer count metric
  elite_partners: {
    name: 'Elite Partner Performance Tiers',
    description: 'Calculate tiered rates for elite partners based on customer acquisition',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-12-31',
      tier_metric: 'customer_count',
      partner_tier_filter: 'elite',
      reward_rule_name: 'Elite Partner Rates',
      include_bonuses: true
    }
  },

  // Monthly performance tracking
  monthly_tracking: {
    name: 'Monthly Performance Tier Tracking',
    description: 'Track partner performance against monthly revenue tiers',
    parameters: {
      performance_start: '2024-01-01',
      performance_end: '2024-01-31',
      tier_metric: 'monthly_revenue',
      include_bonuses: false
    }
  }
};

// Create and export the template instance
export const tieredRateTemplate = new TieredRateTemplate();