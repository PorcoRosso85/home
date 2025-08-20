/**
 * Test for UC1: Partner LTV Ranking (Entity Structure)
 * Business Value: Identify most profitable partners at a glance
 * 
 * This test uses the Entity structure instead of separate Partner/Customer tables.
 * It should initially FAIL because the existing uc1_partner_ltv_ranking.cypher query
 * expects the old Partner/Customer/Subscription table structure.
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

test('UC1: Partner LTV Ranking (Entity) - should rank partners by total customer LTV', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Insert test data using Entity structure
    await insertTestPartners(conn)
    await insertTestCustomers(conn)
    await createPartnerRelationships(conn)
    
    // Insert Contract data (subscriptions) - Entity structure version
    await conn.query(`CREATE (:Contract {id: 1, entity_id: 101, type: 'subscription', recurring_amount: 2000, duration: 25, status: 'active'})`)
    await conn.query(`CREATE (:Contract {id: 2, entity_id: 102, type: 'subscription', recurring_amount: 1500, duration: 20, status: 'active'})`)
    await conn.query(`CREATE (:Contract {id: 3, entity_id: 103, type: 'subscription', recurring_amount: 1000, duration: 20, status: 'active'})`)
    
    // Create HAS_CONTRACT relationships (Entity -> Contract)
    await conn.query(`MATCH (c:Entity {id: 101}), (s:Contract {id: 1}) CREATE (c)-[:HAS_CONTRACT {role: 'owner'}]->(s)`)
    await conn.query(`MATCH (c:Entity {id: 102}), (s:Contract {id: 2}) CREATE (c)-[:HAS_CONTRACT {role: 'owner'}]->(s)`)
    await conn.query(`MATCH (c:Entity {id: 103}), (s:Contract {id: 3}) CREATE (c)-[:HAS_CONTRACT {role: 'owner'}]->(s)`)
    
    // Execute the Entity-aware query (this should PASS - GREEN phase of TDD)
    // The query has been updated to use Entity/Contract structure
    const query = loadQuery('./uc1_partner_ltv_ranking.cypher')
    
    // Execute query and verify results
    const result = await conn.query(query)
    const rows = await result.getAllObjects()
    
    // Verify we got results
    assert(rows.length > 0, 'Should return at least one partner ranking')
    
    // Verify the structure of results
    const firstRow = rows[0]
    assert('partner_name' in firstRow, 'Should have partner_name column')
    assert('customer_count' in firstRow, 'Should have customer_count column') 
    assert('total_ltv' in firstRow, 'Should have total_ltv column')
    
    // Debug: log the actual types
    console.log('Debug - Types:', {
      partner_name: typeof firstRow.partner_name,
      customer_count: typeof firstRow.customer_count,
      total_ltv: typeof firstRow.total_ltv
    })
    console.log('Debug - Values:', firstRow)
    
    // Verify data types and values
    assert(typeof firstRow.partner_name === 'string', 'partner_name should be string')
    // Handle KuzuDB Number object for customer_count
    const customerCount = Number(firstRow.customer_count)
    assert(!isNaN(customerCount), 'customer_count should be a valid number')
    // Handle total_ltv - could be number or null
    if (firstRow.total_ltv !== null) {
      const totalLtv = Number(firstRow.total_ltv)
      assert(!isNaN(totalLtv), 'total_ltv should be a valid number')
    }
    
    // Verify results are ordered by total_ltv DESC
    if (rows.length > 1) {
      for (let i = 0; i < rows.length - 1; i++) {
        const ltv1 = Number(rows[i].total_ltv) || 0
        const ltv2 = Number(rows[i + 1].total_ltv) || 0
        assert(ltv1 >= ltv2, 'Results should be ordered by total_ltv DESC')
      }
    }
    
    console.log('✅ UC1 Entity test passed: Query successfully works with Entity structure')
    console.log('📊 Results:')
    rows.forEach((row, i) => {
      console.log(`   ${i + 1}. ${row.partner_name}: ${row.customer_count} customers, $${row.total_ltv} LTV`)
    })
    
  } finally {
    await close()
  }
})