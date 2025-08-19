/**
 * Test for UC7: Attribution Path Analysis
 * Business Value: Track multi-touchpoint customer attribution across channels
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { 
  setupTestDatabase, 
  loadQuery, 
  insertTestPartners, 
  insertTestCustomers,
  createPartnerRelationships,
  insertTestCampaigns,
  createCampaignInteractions 
} from './test-helper.ts'

test('UC7: Attribution Path Analysis - should analyze multi-touchpoint attribution paths', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    await insertTestCampaigns(conn)
    await createCampaignInteractions(conn)
    
    // Create additional touchpoints for attribution analysis
    await conn.query(`
      CREATE (:Entity {id: 301, name: 'Email Campaign', type: 'campaign', campaign_type: 'email', budget: 3000})
    `)
    await conn.query(`
      CREATE (:Entity {id: 302, name: 'Content Marketing', type: 'campaign', campaign_type: 'content', budget: 7000})
    `)
    
    // Create multi-touchpoint customer journey
    await conn.query(`
      CREATE (:Entity {id: 401, name: 'Attribution Customer', type: 'customer', ltv: 55000, source: 'multi-touch'})
    `)
    
    // Create attribution path: Email -> Partner -> Content -> Customer
    await conn.query(`MATCH (c1:Entity {id: 301}), (cust:Entity {id: 401}) CREATE (c1)-[:INTERACTION {type: 'email_opened', interaction_date: '2024-01-01'}]->(cust)`)
    await conn.query(`MATCH (p:Entity {id: 1}), (cust:Entity {id: 401}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-01-05'}]->(cust)`)
    await conn.query(`MATCH (c2:Entity {id: 302}), (cust:Entity {id: 401}) CREATE (c2)-[:INTERACTION {type: 'content_engaged', interaction_date: '2024-01-10'}]->(cust)`)
    
    // Create conversion event
    await conn.query(`MATCH (cust:Entity {id: 401}) CREATE (cust)-[:INTERACTION {type: 'converted', interaction_date: '2024-01-15'}]->(cust)`)
    
    // Execute query
    const query = loadQuery('./uc7_attribution_path_analysis.cypher')
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify results
    assert(rows.length > 0, 'Should have attribution path results')
    assert(rows[0].customer_name || rows[0].customer_id, 'Should have customer identifier')
    assert(typeof rows[0].path_length === 'number' || rows[0].touchpoint_count, 'Should have path length or touchpoint count')
    
    console.log('✅ UC7 test passed: Attribution path analysis calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})