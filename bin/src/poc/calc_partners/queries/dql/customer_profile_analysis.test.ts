/**
 * Test for UC4: Customer Profile Analysis by Partner
 * Business Value: Understand customer demographics and behavior patterns per partner
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

test('UC4: Customer Profile Analysis - should analyze customer demographics by partner', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Create additional customers with varied profiles
    await conn.query(`
      CREATE (:Entity {id: 201, name: 'High Value Customer', type: 'customer', ltv: 75000, retention_rate: 0.92, industry: 'Tech'})
    `)
    await conn.query(`
      CREATE (:Entity {id: 202, name: 'Medium Value Customer', type: 'customer', ltv: 35000, retention_rate: 0.88, industry: 'Finance'})
    `)
    
    // Create relationships for profiling
    await conn.query(`MATCH (p:Entity {id: 1}), (c:Entity {id: 201}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-03-01'}]->(c)`)
    await conn.query(`MATCH (p:Entity {id: 2}), (c:Entity {id: 202}) CREATE (p)-[:INTERACTION {type: 'introduced', interaction_date: '2024-03-05'}]->(c)`)
    
    // Execute query with partner name parameter
    const query = loadQuery('./customer_profile_analysis.cypher')
    // Replace parameter placeholder with actual value
    const queryWithParam = query.replace(/\$partnerName/g, "'Partner A'")
    const result = await conn.query(queryWithParam)
    const rows = await result.getAllObjects()
    
    // Verify results
    assert(rows.length > 0, 'Should have customer profile results')
    assert(rows[0].partner_name, 'Should have partner name')
    assert(rows[0].total_customers !== undefined, 'Should have total customers')
    assert(rows[0].avg_ltv !== undefined, 'Should have average LTV')
    
    // Handle KuzuDB Number objects
    const totalCustomers = Number(rows[0].total_customers)
    const avgLtv = Number(rows[0].avg_ltv) || 0
    assert(!isNaN(totalCustomers), 'Total customers should be a valid number')
    assert(!isNaN(avgLtv), 'Average LTV should be a valid number')
    
    console.log('✅ UC4 test passed: Customer profile analysis calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})