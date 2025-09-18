/**
 * Test for Cashflow Projection
 * Tests: Quarterly cashflow projection with revenue and reward calculations
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

test('Cashflow Projection - should project quarterly cashflows', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Setup test data
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Test parameters
    const quarterCount = 4  // Project 4 quarters ahead
    
    // Load and execute query
    const query = loadQuery('./cashflow_projection.cypher')
    const queryWithParams = query
      .replace(/\$quarterCount/g, quarterCount.toString())
    
    const result = await conn.query(queryWithParams)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Cashflow projections:', rows)
    
    // Should return results for each quarter
    assert.strictEqual(rows.length, quarterCount, 
                      `Should return ${quarterCount} quarters of projection`)
    
    // Each quarter should have required fields
    rows.forEach((row, index) => {
      assert.strictEqual(row.period, `Q${index + 1}`, `Period should be Q${index + 1}`)
      assert(row.revenue !== undefined, 'Should have revenue')
      assert(row.rewards !== undefined, 'Should have rewards')
      assert(row.netIncome !== undefined, 'Should have net income')
      assert(row.customerBase !== undefined, 'Should have customer base')
      assert(row.profitMarginPercent !== undefined, 'Should have profit margin')
    })
    
    // Verify growth trend (revenue should increase each quarter)
    for (let i = 0; i < rows.length - 1; i++) {
      assert(rows[i + 1].revenue >= rows[i].revenue,
             'Revenue should increase or stay stable each quarter')
      assert(rows[i + 1].customerBase >= rows[i].customerBase,
             'Customer base should grow each quarter')
    }
    
    // Verify financial calculations
    rows.forEach(row => {
      // Net income should be revenue minus rewards
      const calculatedNetIncome = row.revenue - row.rewards
      assert.strictEqual(row.netIncome, calculatedNetIncome, 
                        'Net income should equal revenue minus rewards')
      
      // Profit margin should be positive
      assert(row.profitMarginPercent > 0, 'Profit margin should be positive')
    })
    
    console.log('✅ Cashflow Projection test passed: Quarterly projections calculated successfully')
    await result.close()
  } finally {
    await close()
  }
})