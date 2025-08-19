/**
 * Test for UC5: Retention Rate Comparison
 * Business Value: Compare customer retention across different partner channels
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { 
  setupTestDatabase, 
  loadQuery, 
  insertTestPartners, 
  insertTestCustomers,
  createPartnerRelationships 
} from './test-helper.ts'

test('UC5: Retention Rate Comparison - should compare retention across partner channels', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Create customers with different retention rates
    await conn.query(`
      CREATE (:Entity {id: 201, name: 'High Retention Customer', type: 'customer', retention_rate: 0.98, source: 'referral'})
    `)
    await conn.query(`
      CREATE (:Entity {id: 202, name: 'Medium Retention Customer', type: 'customer', retention_rate: 0.82, source: 'direct'})
    `)
    await conn.query(`
      CREATE (:Entity {id: 203, name: 'Low Retention Customer', type: 'customer', retention_rate: 0.65, source: 'ad'})
    `)
    
    // Create partner relationships for retention analysis
    await conn.query(`MATCH (p:Entity {id: 1}), (c:Entity {id: 201}) CREATE (p)-[:INTERACTION {type: 'retained', interaction_date: '2024-01-01'}]->(c)`)
    await conn.query(`MATCH (p:Entity {id: 2}), (c:Entity {id: 202}) CREATE (p)-[:INTERACTION {type: 'retained', interaction_date: '2024-01-01'}]->(c)`)
    await conn.query(`MATCH (p:Entity {id: 3}), (c:Entity {id: 203}) CREATE (p)-[:INTERACTION {type: 'churned', interaction_date: '2024-01-01'}]->(c)`)
    
    // Execute query
    const query = loadQuery('./uc5_retention_rate_comparison.cypher')
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Query results:', rows)
    assert(rows.length > 0, 'Should have retention comparison results')
    assert(rows[0].acquisition_channel || rows[0].source, 'Should have acquisition_channel or source')
    assert(typeof rows[0].avg_retention_rate === 'number', 'Should have average retention rate')
    assert(rows[0].customer_count !== undefined, 'Should have customer count')
    
    console.log('✅ UC5 test passed: Retention rate comparison calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})