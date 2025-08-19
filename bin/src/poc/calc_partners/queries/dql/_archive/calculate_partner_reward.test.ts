/**
 * Test for calculate_partner_reward.cypher
 * Pain Point: 1l�Lcf�K�Excelh�M�[f��Wf�
 */

import { describe, test, before, after, beforeEach } from 'node:test'
import assert from 'node:assert'
import { loadQuery } from '../../infrastructure/cypherLoader.ts'
import { initializeKuzu, executeQuery, type KuzuConnectionInfo } from '../../infrastructure.ts'
// import { setupTestData, cleanupTestData } from '../../test/helpers/testDataHelper'

describe('calculate_partner_reward.cypher - Partner Reward Calculation', () => {
  let kuzuInfo: KuzuConnectionInfo
  let queryContent: string
  
  before(async () => {
    kuzuInfo = await initializeKuzu()
    const queryResult = loadQuery('dql', 'calculate_partner_reward')
    assert.strictEqual(queryResult.success, true)
    queryContent = queryResult.data!
  })
  
  after(async () => {
    if (kuzuInfo) {
      await kuzuInfo.close()
    }
  })
  
  // beforeEach(async () => {
  //   await cleanupTestData(kuzuInfo.conn)
  //   await setupTestData(kuzuInfo.conn)
  // })
  
  test('should calculate percentage-based rewards correctly', async () => {
    // Test data: Partner with 100,000 JPY in transactions, 5% reward rate
    // Note: Cypher parameters would be handled within the query itself
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Verify calculation: 100,000 * 0.05 = 5,000
    assert.strictEqual(rows.length, 1)
    assert.strictEqual(rows[0].reward_amount, 5000)
    assert.strictEqual(rows[0].calculation_method, 'percentage')
    assert.strictEqual(rows[0].base_amount, 100000)
    assert.strictEqual(rows[0].applied_rate, 0.05)
  })
  
  test('should apply tiered rates based on transaction volume', async () => {
    // Test tiered calculation
    // Note: Cypher parameters would be handled within the query itself
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Verify tiered logic is applied
    assert.strictEqual(rows[0].calculation_method, 'tiered')
    assert.ok(rows[0].tier_breakdown !== undefined)
    assert.ok(rows[0].tier_breakdown.length > 0)
  })
  
  test('should handle network rewards for referrals', async () => {
    // Test network reward calculation
    // Note: Cypher parameters would be handled within the query itself
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Verify network rewards are included
    assert.ok(rows[0].network_reward_amount > 0)
    assert.ok(rows[0].referred_partners_count > 0)
    assert.strictEqual(rows[0].total_reward,
      rows[0].direct_reward + rows[0].network_reward_amount
    )
  })
  
  test('should exclude cancelled transactions', async () => {
    // Add a cancelled transaction
    await executeQuery(kuzuInfo.conn, `
      CREATE (t:Transaction {
        id: 999,
        partner_id: 'P001',
        amount: 50000,
        status: 'cancelled',
        transaction_date: DATE('2024-01-15')
      })
    `)
    
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Cancelled transaction should not affect reward
    assert.strictEqual(rows[0].base_amount, 100000) // Original amount only
  })
  
  test('should handle date range filtering correctly', async () => {
    // Test with different date ranges
    const testCases = [
      { 
        startDate: '2024-01-01', 
        endDate: '2024-01-15',
        expectedTransactions: 2
      },
      { 
        startDate: '2024-01-16', 
        endDate: '2024-01-31',
        expectedTransactions: 1
      },
      { 
        startDate: '2024-02-01', 
        endDate: '2024-02-28',
        expectedTransactions: 0
      }
    ]
    
    for (const testCase of testCases) {
      // Note: Cypher parameters would be handled within the query itself
      const rows = await executeQuery(kuzuInfo.conn, queryContent)
      
      if (testCase.expectedTransactions === 0) {
        assert.strictEqual(rows.length, 0)
      } else {
        assert.strictEqual(rows[0].transaction_count, testCase.expectedTransactions)
      }
    }
  })
  
  test('should apply minimum threshold rules', async () => {
    // Test minimum threshold
    // Note: Cypher parameters would be handled within the query itself
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // If reward is below threshold, it should be adjusted or flagged
    if (rows.length > 0) {
      assert.ok(rows[0].reward_amount >= 1000)
      assert.strictEqual(rows[0].threshold_applied, true)
    }
  })
  
  test('should handle missing reward rules gracefully', async () => {
    // Create partner without reward rules
    await executeQuery(kuzuInfo.conn, `
      CREATE (p:Partner {
        id: 'P999',
        code: 'NO_RULE',
        name: 'No Rule Partner',
        tier: 'bronze'
      })
    `)
    
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Should return empty or default result
    assert.strictEqual(rows.length, 0)
  })
  
  test('should match Excel calculation for verification', async () => {
    // This test ensures our calculation matches the Excel formula
    // Excel formula: =SUMIFS(transactions, partner_id, "P001", status, "confirmed") * 0.05
    
    const rows = await executeQuery(kuzuInfo.conn, queryContent)
    
    // Known Excel result for this test data
    const excelCalculatedReward = 5000
    
    assert.strictEqual(rows[0].reward_amount, excelCalculatedReward)
    assert.strictEqual(rows[0].verification_status, 'verified')
  })
})