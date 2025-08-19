/**
 * Test Helper for KuzuDB DQL Tests
 * Provides common setup and utilities for all UC tests
 */

import { createRequire } from 'module'
import { readFileSync } from 'fs'

const require = createRequire(import.meta.url)
const kuzu = require('kuzu-wasm/nodejs')

export interface TestContext {
  db: any
  conn: any
  close: () => Promise<void>
}

/**
 * Initialize KuzuDB test database with common schema
 */
export async function setupTestDatabase(): Promise<TestContext> {
  const db = new kuzu.Database(':memory:', 1 << 30)
  const conn = new kuzu.Connection(db, 4)
  
  // Create base schema matching schema.cypher
  await conn.query(`
    CREATE NODE TABLE Entity(
      id INT64,
      code STRING,
      name STRING,
      type STRING,
      industry STRING,
      ltv DOUBLE,
      retention_rate DOUBLE,
      source STRING,
      budget DOUBLE,
      campaign_type STRING,
      tier STRING,
      value DOUBLE,
      PRIMARY KEY (id)
    )
  `)
  
  await conn.query(`
    CREATE NODE TABLE Contract(
      id INT64,
      entity_id INT64,
      type STRING,
      amount DOUBLE,
      recurring_amount DOUBLE,
      duration INT32,
      status STRING,
      PRIMARY KEY (id)
    )
  `)
  
  await conn.query(`
    CREATE REL TABLE INTERACTION(
      FROM Entity TO Entity,
      type STRING,
      interaction_date STRING,
      depth INT32,
      status STRING,
      metadata STRING
    )
  `)
  
  await conn.query(`
    CREATE REL TABLE HAS_CONTRACT(
      FROM Entity TO Contract,
      role STRING
    )
  `)
  
  return {
    db,
    conn,
    close: async () => {
      await conn.close()
      await db.close()
      await kuzu.close()
    }
  }
}

/**
 * Load and prepare Cypher query from file
 */
export function loadQuery(filename: string): string {
  const queryContent = readFileSync(filename, 'utf-8')
  return queryContent
    .split('\n')
    .filter(line => {
      const trimmed = line.trim()
      return trimmed && 
             !trimmed.startsWith('//') && 
             !trimmed.startsWith('--') &&
             !trimmed.startsWith('/*')
    })
    .filter(line => !line.includes('┌') && !line.includes('│') && !line.includes('└'))
    .join(' ')
    .replace(/;.*$/, '')
    .replace(/\/\*[\s\S]*?\*\//g, '') // Remove block comments
}

/**
 * Insert test data for partners
 */
export async function insertTestPartners(conn: any) {
  await conn.query(`CREATE (:Entity {id: 1, name: 'Partner A', type: 'partner', tier: 'Gold'})`)
  await conn.query(`CREATE (:Entity {id: 2, name: 'Partner B', type: 'partner', tier: 'Silver'})`)
  await conn.query(`CREATE (:Entity {id: 3, name: 'Partner C', type: 'partner', tier: 'Bronze'})`)
}

/**
 * Insert test data for customers
 */
export async function insertTestCustomers(conn: any) {
  await conn.query(`CREATE (:Entity {id: 101, name: 'Customer 1', type: 'customer', ltv: 50000, retention_rate: 0.95, source: 'referral', industry: 'Tech'})`)
  await conn.query(`CREATE (:Entity {id: 102, name: 'Customer 2', type: 'customer', ltv: 30000, retention_rate: 0.85, source: 'referral', industry: 'Finance'})`)
  await conn.query(`CREATE (:Entity {id: 103, name: 'Customer 3', type: 'customer', ltv: 20000, retention_rate: 0.75, source: 'direct', industry: 'Retail'})`)
  await conn.query(`CREATE (:Entity {id: 104, name: 'Customer 4', type: 'customer', ltv: 40000, retention_rate: 0.70, source: 'ad', industry: 'Tech'})`)
}

/**
 * Create partner-customer relationships
 */
export async function createPartnerRelationships(conn: any) {
  await conn.query(`MATCH (p:Entity {id: 1}), (c:Entity {id: 101}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-01-15'}]->(c)`)
  await conn.query(`MATCH (p:Entity {id: 1}), (c:Entity {id: 102}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-02-01'}]->(c)`)
  await conn.query(`MATCH (p:Entity {id: 2}), (c:Entity {id: 103}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-01-20'}]->(c)`)
  await conn.query(`MATCH (p:Entity {id: 3}), (c:Entity {id: 104}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-02-10'}]->(c)`)
}

/**
 * Insert test campaigns for attribution analysis
 */
export async function insertTestCampaigns(conn: any) {
  await conn.query(`CREATE (:Entity {id: 201, name: 'Web Campaign', type: 'campaign', campaign_type: 'web', budget: 10000})`)
  await conn.query(`CREATE (:Entity {id: 202, name: 'Social Campaign', type: 'campaign', campaign_type: 'social', budget: 5000})`)
}

/**
 * Create campaign interactions
 */
export async function createCampaignInteractions(conn: any) {
  await conn.query(`MATCH (c:Entity {id: 201}), (cust:Entity {id: 101}) CREATE (c)-[:INTERACTION {type: 'clicked', interaction_date: '2024-01-10'}]->(cust)`)
  await conn.query(`MATCH (c:Entity {id: 202}), (cust:Entity {id: 102}) CREATE (c)-[:INTERACTION {type: 'clicked', interaction_date: '2024-02-05'}]->(cust)`)
}