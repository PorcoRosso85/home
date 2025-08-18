/**
 * Partner Reward Calculation Template
 * 
 * Calculates rewards for partners based on their transactions and applicable reward rules.
 * Supports different reward types: fixed, percentage, tiered, and network-based rewards.
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Template for calculating partner rewards based on transactions and reward rules
 */
export class PartnerRewardTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'calculate_partner_reward',
      'Calculate rewards for partners based on their transactions and applicable reward rules within a specified period',
      'reward',
      [
        TemplateHelpers.createParameter(
          'partner_id',
          'string',
          'Partner ID to calculate rewards for',
          {
            required: true,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('calculation'),
        TemplateHelpers.createParameter(
          'reward_rule_type',
          'string',
          'Type of reward rule to apply',
          {
            required: false,
            examples: ['fixed', 'percentage', 'tiered', 'network']
          }
        ),
        TemplateHelpers.createParameter(
          'transaction_type',
          'string',
          'Filter by specific transaction type',
          {
            required: false,
            examples: ['subscription', 'upgrade', 'renewal', 'referral']
          }
        ),
        TemplateHelpers.createParameter(
          'min_transaction_amount',
          'decimal',
          'Minimum transaction amount to include in calculations',
          {
            required: false,
            min: 0,
            default: 0,
            examples: [100, 500, 1000]
          }
        )
      ],
      {
        painPoint: 'SaaS companies need to accurately calculate partner rewards across different rule types and transaction scenarios, but manual calculations are error-prone and time-consuming',
        tags: ['reward', 'partner', 'calculation', 'commission', 'payout']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const {
      partner_id,
      calculation_start,
      calculation_end,
      reward_rule_type,
      transaction_type,
      min_transaction_amount
    } = params;

    let query = `
// Calculate Partner Rewards
MATCH (p:Partner {code: '${this.escapeString(partner_id)}'})-[:APPLIES_RULE]->(rr:RewardRule)
MATCH (p)-[:GENERATES]->(t:Transaction)
WHERE t.transaction_date >= date('${this.formatDate(calculation_start)}')
  AND t.transaction_date <= date('${this.formatDate(calculation_end)}')
  AND t.status = 'confirmed'`;

    // Add reward rule type filter
    if (reward_rule_type) {
      query += `\n  AND rr.type = '${this.escapeString(reward_rule_type)}'`;
    }

    // Add transaction type filter
    if (transaction_type) {
      query += `\n  AND t.type = '${this.escapeString(transaction_type)}'`;
    }

    // Add minimum transaction amount filter
    if (min_transaction_amount > 0) {
      query += `\n  AND t.amount >= ${min_transaction_amount}`;
    }

    query += `

// Calculate rewards based on rule type
WITH p, rr, t,
  CASE rr.type
    WHEN 'fixed' THEN rr.base_amount
    WHEN 'percentage' THEN t.amount * rr.base_rate
    ELSE 0
  END AS calculated_reward

// For tiered rules, we need to check thresholds
OPTIONAL MATCH (rr)-[:HAS_THRESHOLD]->(th:Threshold)
WHERE th.metric = 'transaction_amount'
  AND t.amount >= th.min_value
  AND (th.max_value IS NULL OR t.amount <= th.max_value)

WITH p, rr, t, calculated_reward, th,
  CASE 
    WHEN rr.type = 'tiered' AND th IS NOT NULL THEN 
      t.amount * th.rate + COALESCE(th.bonus, 0)
    ELSE calculated_reward
  END AS final_reward

// Network-based rewards (referral depth multiplier)
OPTIONAL MATCH (p)<-[:REFERS*1..3]-(referrer:Partner)
WITH p, rr, t, final_reward,
  CASE 
    WHEN rr.type = 'network' THEN 
      final_reward * (1 + (0.1 * COUNT(DISTINCT referrer)))
    ELSE final_reward
  END AS network_adjusted_reward

RETURN 
  p.code AS partner_id,
  p.name AS partner_name,
  rr.name AS rule_name,
  rr.type AS rule_type,
  COUNT(t) AS qualifying_transactions,
  SUM(t.amount) AS total_transaction_value,
  SUM(network_adjusted_reward) AS total_reward_amount,
  AVG(network_adjusted_reward) AS avg_reward_per_transaction,
  MIN(t.transaction_date) AS first_qualifying_transaction,
  MAX(t.transaction_date) AS last_qualifying_transaction,
  '${this.formatDate(calculation_start)}' AS calculation_period_start,
  '${this.formatDate(calculation_end)}' AS calculation_period_end

ORDER BY total_reward_amount DESC`;

    return query;
  }
}

// Example usage scenarios
export const rewardCalculationExamples = {
  // Basic reward calculation for a partner
  basic: {
    name: 'Basic Partner Reward Calculation',
    description: 'Calculate all rewards for a partner in the last month',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      calculation_start: '2024-01-01',
      calculation_end: '2024-01-31'
    }
  },

  // Percentage-based rewards only
  percentage: {
    name: 'Percentage Reward Calculation',
    description: 'Calculate only percentage-based rewards for subscription transactions',
    parameters: {
      partner_id: 'PARTNER_X7Y8Z9W0',
      calculation_start: '2024-01-01',
      calculation_end: '2024-12-31',
      reward_rule_type: 'percentage',
      transaction_type: 'subscription',
      min_transaction_amount: 500
    }
  },

  // Tiered reward calculation
  tiered: {
    name: 'Tiered Reward Analysis',
    description: 'Analyze tiered rewards for high-value transactions',
    parameters: {
      partner_id: 'PARTNER_B5C6D7E8',
      calculation_start: '2024-01-01',
      calculation_end: '2024-12-31',
      reward_rule_type: 'tiered',
      min_transaction_amount: 1000
    }
  }
};

// Create and export the template instance
export const partnerRewardTemplate = new PartnerRewardTemplate();