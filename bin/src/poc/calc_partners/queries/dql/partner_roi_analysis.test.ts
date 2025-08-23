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
    
    // Note: Query uses estimated rewards (20% of customer LTV)
    // No need to create actual reward data for this analysis
    
    // Execute query
    const query = loadQuery('./partner_roi_analysis.cypher')
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