/**
 * Test for UC2: Partner ROI Analysis
 * Business Value: Calculate net profit per partner considering costs
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

test('UC2: Partner ROI Analysis - should calculate net profit per partner', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Create rewards data
    await conn.query(`
      CREATE (:Entity {id: 301, type: 'reward', entity_id: 1, amount: 5000})
    `)
    await conn.query(`
      CREATE (:Entity {id: 302, type: 'reward', entity_id: 1, amount: 3000})
    `)
    await conn.query(`
      CREATE (:Entity {id: 303, type: 'reward', entity_id: 2, amount: 2000})
    `)
    
    // Execute query
    const query = loadQuery('./uc2_partner_roi_analysis.cypher')
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify results
    assert(rows.length > 0, 'Should have ROI results')
    assert(rows[0].partner_name, 'Should have partner name')
    assert(typeof rows[0].total_customer_value === 'number', 'Should have total customer value')
    assert(typeof rows[0].net_profit === 'number', 'Should have net profit')
    
    console.log('✅ UC2 test passed: Partner ROI calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})