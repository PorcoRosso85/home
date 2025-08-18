/**
 * Example Query Template - Partner Revenue Analysis
 * 
 * This is a demonstration of how to create a concrete query template
 * using the base template system. It shows all the key features:
 * - Parameter definition with validation
 * - Query generation
 * - Usage examples
 */

import { BaseQueryTemplate, TemplateHelpers, ValidationPatterns } from './index.js';
import type { QueryContext } from './types.js';

/**
 * Example template: Get partner revenue within a date range
 */
export class PartnerRevenueTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'partner_revenue_analysis',
      'Analyze partner revenue performance within a specified date range with optional filtering by partner type',
      'revenue',
      [
        TemplateHelpers.createParameter(
          'partner_id',
          'string',
          'Unique identifier for the partner',
          {
            required: false,
            pattern: ValidationPatterns.PARTNER_ID,
            examples: ['PARTNER_A1B2C3D4', 'PARTNER_X7Y8Z9W0']
          }
        ),
        ...TemplateHelpers.createDateRange('revenue'),
        TemplateHelpers.createParameter(
          'partner_type',
          'string',
          'Type of partner to filter by',
          {
            required: false,
            examples: ['premium', 'standard', 'trial']
          }
        ),
        TemplateHelpers.createParameter(
          'min_revenue',
          'decimal',
          'Minimum revenue threshold',
          {
            required: false,
            min: 0,
            default: 0,
            examples: [1000, 5000, 10000]
          }
        )
      ],
      {
        painPoint: 'Business analysts need quick insights into partner revenue performance but struggle with complex SQL queries',
        tags: ['revenue', 'partner', 'analytics', 'performance', 'financial']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { partner_id, revenue_start, revenue_end, partner_type, min_revenue } = params;

    let query = `
MATCH (p:Partner)-[:GENERATES]->(r:Revenue)
WHERE r.date >= date('${this.formatDate(revenue_start)}')
  AND r.date <= date('${this.formatDate(revenue_end)}')`;

    // Add partner ID filter if provided
    if (partner_id) {
      query += `\n  AND p.id = '${this.escapeString(partner_id)}'`;
    }

    // Add partner type filter if provided
    if (partner_type) {
      query += `\n  AND p.type = '${this.escapeString(partner_type)}'`;
    }

    // Add minimum revenue filter
    if (min_revenue > 0) {
      query += `\n  AND r.amount >= ${min_revenue}`;
    }

    query += `
RETURN p.id AS partner_id,
       p.name AS partner_name,
       p.type AS partner_type,
       sum(r.amount) AS total_revenue,
       count(r) AS transaction_count,
       avg(r.amount) AS avg_transaction_value,
       min(r.date) AS first_transaction,
       max(r.date) AS last_transaction
ORDER BY total_revenue DESC`;

    return query;
  }
}

// Example usage and registration
export const exampleUsage = {
  // Basic usage with date range only
  basic: {
    name: 'Basic Revenue Analysis',
    description: 'Get all partner revenue for a specific month',
    parameters: {
      revenue_start: '2024-01-01',
      revenue_end: '2024-01-31'
    }
  },

  // Filtered by partner type and minimum revenue
  filtered: {
    name: 'Premium Partners Above Threshold',
    description: 'Analyze premium partners with revenue above $5000',
    parameters: {
      revenue_start: '2024-01-01',
      revenue_end: '2024-12-31',
      partner_type: 'premium',
      min_revenue: 5000
    }
  },

  // Specific partner analysis
  specific: {
    name: 'Specific Partner Deep Dive',
    description: 'Analyze a specific partner\'s revenue performance',
    parameters: {
      partner_id: 'PARTNER_A1B2C3D4',
      revenue_start: '2024-01-01',
      revenue_end: '2024-12-31'
    }
  }
};

// Create and export the template instance
export const partnerRevenueTemplate = new PartnerRevenueTemplate();