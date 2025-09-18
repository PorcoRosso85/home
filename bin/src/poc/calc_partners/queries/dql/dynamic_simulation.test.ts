/**
 * Test for Dynamic Partner Simulation
 * Tests: Multi-month partner growth simulation with various scenarios
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

test('Dynamic Simulation - should simulate partner growth over multiple months', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Setup test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Test parameters
    const partnerId = 1
    const monthsToSimulate = 6
    const growthRate = 0.15  // 15% growth rate
    const churnRate = 0.05   // 5% churn rate
    
    // Load and execute query with parameter replacement
    const query = loadQuery('./dynamic_simulation.cypher')
    const queryWithParams = query
      .replace(/\$partnerId/g, partnerId.toString())
      .replace(/\$monthsToSimulate/g, monthsToSimulate.toString())
      .replace(/\$growthRate/g, growthRate.toString())
      .replace(/\$churnRate/g, churnRate.toString())
    
    const result = await conn.query(queryWithParams)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Simulation results for first 3 months:', rows.slice(0, 3))
    
    // Should return results for each month
    assert.strictEqual(rows.length, monthsToSimulate, 
                      `Should return ${monthsToSimulate} months of simulation`)
    
    // Each month should have required fields
    rows.forEach((row, index) => {
      assert.strictEqual(row.month, index + 1, `Month should be ${index + 1}`)
      assert(row.partnerName, 'Should have partner name')
      assert(row.customerCount !== undefined, 'Should have customer count')
      assert(row.totalRevenue !== undefined, 'Should have total revenue')
      assert(row.growthStatus, 'Should have growth status')
    })
    
    // Verify growth trend (with positive net growth, later months should have more customers)
    const netGrowth = growthRate - churnRate
    if (netGrowth > 0) {
      for (let i = 0; i < rows.length - 1; i++) {
        assert(rows[i + 1].customerCount >= rows[i].customerCount,
               'Customer count should increase or stay stable with positive net growth')
      }
    }
    
    console.log('✅ Dynamic Simulation test passed: Growth simulation completed successfully')
    await result.close()
  } finally {
    await close()
  }
})

test('Dynamic Simulation - should handle declining scenario', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Setup test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Test parameters for declining scenario
    const partnerId = 2
    const monthsToSimulate = 3
    const growthRate = 0.02   // 2% growth rate
    const churnRate = 0.10    // 10% churn rate (higher than growth)
    
    // Load and execute query
    const query = loadQuery('./dynamic_simulation.cypher')
    const queryWithParams = query
      .replace(/\$partnerId/g, partnerId.toString())
      .replace(/\$monthsToSimulate/g, monthsToSimulate.toString())
      .replace(/\$growthRate/g, growthRate.toString())
      .replace(/\$churnRate/g, churnRate.toString())
    
    const result = await conn.query(queryWithParams)
    const rows = await result.getAllObjects()
    
    // Verify declining trend
    assert.strictEqual(rows.length, monthsToSimulate, 'Should return all months')
    
    // With negative net growth, customer count should decrease
    const netGrowth = growthRate - churnRate
    if (netGrowth < 0) {
      for (let i = 0; i < rows.length - 1; i++) {
        assert(rows[i + 1].customerCount <= rows[i].customerCount,
               'Customer count should decrease with negative net growth')
      }
    }
    
    console.log('✅ Declining scenario test passed')
    await result.close()
  } finally {
    await close()
  }
})