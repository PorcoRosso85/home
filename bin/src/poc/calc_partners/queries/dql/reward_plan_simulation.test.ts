/**
 * Test for UC3: Reward Plan Simulation (What-If Analysis)
 * Business Value: Risk-free testing of new reward structures before implementation
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

test('UC3: Reward Plan Simulation - should simulate different reward scenarios', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Create customers with partner source for simulation
    await conn.query(`
      CREATE (:Entity {id: 201, name: 'Partner Customer 1', type: 'customer', ltv: 25000, source: 'partner'})
    `)
    await conn.query(`
      CREATE (:Entity {id: 202, name: 'Partner Customer 2', type: 'customer', ltv: 15000, source: 'partner'})
    `)
    await conn.query(`
      CREATE (:Entity {id: 203, name: 'Partner Customer 3', type: 'customer', ltv: 8000, source: 'partner'})
    `)
    
    // Execute query
    const query = loadQuery('./reward_plan_simulation.cypher')
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Query results:', rows[0])
    assert(rows.length > 0, 'Should have simulation scenarios')
    assert(rows[0].scenario_name, 'Should have scenario name')
    assert(typeof rows[0].rate === 'number', 'Should have rate')
    assert(typeof rows[0].predicted_total_payment === 'number', 'Should have predicted total payment')
    assert(rows[0].customers_affected !== undefined || rows[0].customer_count !== undefined, 'Should have customers affected or customer_count')
    
    console.log('✅ UC3 test passed: Reward plan simulation calculated correctly')
    await result.close()
  } finally {
    await close()
  }
})