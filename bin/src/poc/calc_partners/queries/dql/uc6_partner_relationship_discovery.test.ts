/**
 * Test for UC6: Partner Relationship Discovery
 * Business Value: Identify partner network relationships and collaboration opportunities
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

test('UC6: Partner Relationship Discovery - should discover partner network relationships', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Create additional partners for network analysis
    await conn.query(`CREATE (:Entity {id: 4, name: 'Partner D', type: 'partner', tier: 'Gold'})`)
    await conn.query(`CREATE (:Entity {id: 5, name: 'Partner E', type: 'partner', tier: 'Silver'})`)
    
    // Create partner-to-partner relationships
    await conn.query(`MATCH (p1:Entity {id: 1}), (p2:Entity {id: 2}) CREATE (p1)-[:INTERACTION {type: 'collaboration', interaction_date: '2024-01-15', depth: 1}]->(p2)`)
    await conn.query(`MATCH (p2:Entity {id: 2}), (p3:Entity {id: 3}) CREATE (p2)-[:INTERACTION {type: 'referral', interaction_date: '2024-02-01', depth: 2}]->(p3)`)
    await conn.query(`MATCH (p1:Entity {id: 1}), (p4:Entity {id: 4}) CREATE (p1)-[:INTERACTION {type: 'joint_venture', interaction_date: '2024-02-10', depth: 1}]->(p4)`)
    
    // Create shared customers between partners
    await conn.query(`
      CREATE (:Entity {id: 201, name: 'Shared Customer 1', type: 'customer', ltv: 45000})
    `)
    await conn.query(`MATCH (p:Entity {id: 1}), (c:Entity {id: 201}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-01-01'}]->(c)`)
    await conn.query(`MATCH (p:Entity {id: 2}), (c:Entity {id: 201}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-01-15'}]->(c)`)
    
    // Execute query
    const query = loadQuery('./uc6_partner_relationship_discovery.cypher')
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify results
    assert(rows.length > 0, 'Should have partner relationship results')
    assert(rows[0].partner1_name || rows[0].source_partner, 'Should have first partner name')
    assert(rows[0].partner2_name || rows[0].target_partner, 'Should have second partner name')
    
    console.log('✅ UC6 test passed: Partner relationship discovery calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})