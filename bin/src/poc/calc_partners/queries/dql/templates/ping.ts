/**
 * Ping Query Template
 * 
 * Simple connectivity and health check template for testing database
 * connections and system availability. Provides basic system information
 * and performance metrics for monitoring purposes.
 */

import { BaseQueryTemplate } from './base.js';
import type { QueryContext } from './types.js';

/**
 * Simple template for database connectivity and health checks
 */
export class PingTemplate extends BaseQueryTemplate {
  constructor() {
    super(
      'ping',
      'Simple connectivity test and system health check for database monitoring and troubleshooting',
      'system',
      [
        {
          name: 'include_stats',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include basic database statistics in ping response',
          examples: [true, false]
        },
        {
          name: 'include_counts',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Include node/relationship counts for system overview',
          examples: [true, false]
        },
        {
          name: 'test_performance',
          type: 'boolean',
          required: false,
          default: false,
          description: 'Run basic performance test with timing',
          examples: [true, false]
        }
      ],
      {
        painPoint: 'System monitoring requires simple health checks to verify database connectivity and basic system status',
        tags: ['ping', 'health', 'connectivity', 'monitoring', 'system']
      }
    );
  }

  protected generateQuery(params: Record<string, any>, context?: QueryContext): string {
    const { 
      include_stats,
      include_counts,
      test_performance
    } = params;

    let query = `
// Database Ping and Health Check
WITH datetime() as ping_timestamp,
     'OK' as status`;

    // Add basic counts if requested
    if (include_counts) {
      query += `
// Get basic node counts for system overview
OPTIONAL MATCH (p:Partner)
OPTIONAL MATCH (c:Customer) 
OPTIONAL MATCH (r:Revenue)
OPTIONAL MATCH (t:Transaction)

WITH ping_timestamp, status,
     count(distinct p) as partner_count,
     count(distinct c) as customer_count,
     count(distinct r) as revenue_count,
     count(distinct t) as transaction_count`;
    }

    // Add performance test if requested
    if (test_performance) {
      query += `
// Simple performance test - create and delete a test node
CREATE (test:PingTest {id: 'ping_' + toString(timestamp()), created: ping_timestamp})
WITH ping_timestamp, status${include_counts ? ', partner_count, customer_count, revenue_count, transaction_count' : ''}, test

DELETE test
WITH ping_timestamp, status${include_counts ? ', partner_count, customer_count, revenue_count, transaction_count' : ''}, 
     duration.between(ping_timestamp, datetime()).milliseconds as performance_test_ms`;
    }

    // Build response
    query += `
RETURN {
  ping: {
    status: status,
    timestamp: toString(ping_timestamp),
    server_time: toString(datetime()),
    response: 'pong'
  }`;

    if (include_stats) {
      query += `,
  system_info: {
    database_available: true,
    query_engine: 'Cypher',
    response_generated: toString(datetime())
  }`;
    }

    if (include_counts) {
      query += `,
  data_summary: {
    partners: partner_count,
    customers: customer_count,
    revenue_records: revenue_count,
    transactions: transaction_count,
    total_entities: partner_count + customer_count + revenue_count + transaction_count
  }`;
    }

    if (test_performance) {
      query += `,
  performance: {
    test_duration_ms: performance_test_ms,
    status: CASE 
      WHEN performance_test_ms < 100 THEN 'excellent'
      WHEN performance_test_ms < 500 THEN 'good'
      WHEN performance_test_ms < 1000 THEN 'acceptable'
      ELSE 'slow'
    END
  }`;
    }

    query += `
} as ping_response`;

    return query;
  }
}

// Example usage scenarios
export const pingUsage = {
  // Simple connectivity test
  simple_ping: {
    name: 'Simple Ping',
    description: 'Basic connectivity test without additional data',
    parameters: {
      include_stats: false,
      include_counts: false,
      test_performance: false
    }
  },

  // Health check with system information
  health_check: {
    name: 'System Health Check',
    description: 'Comprehensive health check with system stats and counts',
    parameters: {
      include_stats: true,
      include_counts: true,
      test_performance: false
    }
  },

  // Performance monitoring ping
  performance_ping: {
    name: 'Performance Monitoring Ping',
    description: 'Ping with performance testing for monitoring response times',
    parameters: {
      include_stats: true,
      include_counts: true,
      test_performance: true
    }
  },

  // Minimal monitoring probe
  minimal_probe: {
    name: 'Minimal Monitoring Probe',
    description: 'Lightweight probe for frequent monitoring checks',
    parameters: {
      include_stats: false,
      include_counts: false,
      test_performance: false
    }
  }
};

// Create and export the template instance
export const pingTemplate = new PingTemplate();