/**
 * Test for calculate_partner_reward.cypher
 * Pain Point: 1l�Lcf�K�Excelh�M�[f��Wf�
 */

import { describe, test, beforeEach } from 'node:test'
import assert from 'node:assert'
import { loadQuery } from '../../infrastructure/cypherLoader'
import { getConnection } from '../../infrastructure/db'
import { setupTestData, cleanupTestData } from '../../test/helpers/testDataHelper'
import type { Database } from 'kuzu-wasm'

describe('calculate_partner_reward.cypher - Partner Reward Calculation', () => {
  let conn: Database
  let queryContent: string
  
  test.before(async () => {
    conn = await getConnection()
    const queryResult = await loadQuery('dql', 'calculate_partner_reward')
    assert.strictEqual(queryResult.success, true)
    queryContent = queryResult.data!
  })
  
  test.after(async () => {
    if (conn) {
      await conn.close()
    }
  })
  
  test.beforeEach(async () => {
    await cleanupTestData(conn)
    await setupTestData(conn)
  })
  
  test('should calculate percentage-based rewards correctly', async () => {
    // Test data: Partner with 100,000 JPY in transactions, 5% reward rate
    const result = await conn.query(queryContent, {
      partnerId: 'P001',
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      rewardType: 'percentage'
    })
    const rows = await result.getAll()
    
    // Verify calculation: 100,000 * 0.05 = 5,000
    assert.strictEqual(rows.length, 1)
    assert.strictEqual(rows[0].reward_amount, 5000)
    assert.strictEqual(rows[0].calculation_method, 'percentage')
    assert.strictEqual(rows[0].base_amount, 100000)
    assert.strictEqual(rows[0].applied_rate, 0.05)
  })
  
  test('should apply tiered rates based on transaction volume', async () => {
    // Test tiered calculation
    const result = await conn.query(queryContent, {
      partnerId: 'P002',
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      rewardType: 'tiered'
    })
    const rows = await result.getAll()
    
    // Verify tiered logic is applied
    assert.strictEqual(rows[0].calculation_method, 'tiered')
    assert.ok(rows[0].tier_breakdown !== undefined)
    assert.ok(rows[0].tier_breakdown.length > 0)
  })
  
  test('should handle network rewards for referrals', async () => {
    // Test network reward calculation
    const result = await conn.query(queryContent, {
      partnerId: 'P005', // Network leader
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      includeNetworkRewards: true,
      networkDepth: 2
    })
    const rows = await result.getAll()
    
    // Verify network rewards are included
    assert.ok(rows[0].network_reward_amount > 0)
    assert.ok(rows[0].referred_partners_count > 0)
    assert.strictEqual(rows[0].total_reward,
      rows[0].direct_reward + rows[0].network_reward_amount
    )
  })
  
  test('should exclude cancelled transactions', async () => {
    // Add a cancelled transaction
    await conn.query(`
      CREATE (t:Transaction {
        id: 999,
        partner_id: 'P001',
        amount: 50000,
        status: 'cancelled',
        transaction_date: DATE('2024-01-15')
      })
    `)
    
    const result = await conn.query(queryContent, {
      partnerId: 'P001',
      startDate: '2024-01-01',
      endDate: '2024-01-31'
    })
    const rows = await result.getAll()
    
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
      const result = await conn.query(queryContent, {
        partnerId: 'P001',
        ...testCase
      })
      const rows = await result.getAll()
      
      if (testCase.expectedTransactions === 0) {
        assert.strictEqual(rows.length, 0)
      } else {
        assert.strictEqual(rows[0].transaction_count, testCase.expectedTransactions)
      }
    }
  })
  
  test('should apply minimum threshold rules', async () => {
    // Test minimum threshold
    const result = await conn.query(queryContent, {
      partnerId: 'P003', // Bronze partner with low transactions
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      minRewardAmount: 1000
    })
    const rows = await result.getAll()
    
    // If reward is below threshold, it should be adjusted or flagged
    if (rows.length > 0) {
      assert.ok(rows[0].reward_amount >= 1000)
      assert.strictEqual(rows[0].threshold_applied, true)
    }
  })
  
  test('should handle missing reward rules gracefully', async () => {
    // Create partner without reward rules
    await conn.query(`
      CREATE (p:Partner {
        id: 'P999',
        code: 'NO_RULE',
        name: 'No Rule Partner',
        tier: 'bronze'
      })
    `)
    
    const result = await conn.query(queryContent, {
      partnerId: 'P999',
      startDate: '2024-01-01',
      endDate: '2024-01-31'
    })
    const rows = await result.getAll()
    
    // Should return empty or default result
    assert.strictEqual(rows.length, 0)
  })
  
  test('should match Excel calculation for verification', async () => {
    // This test ensures our calculation matches the Excel formula
    // Excel formula: =SUMIFS(transactions, partner_id, "P001", status, "confirmed") * 0.05
    
    const result = await conn.query(queryContent, {
      partnerId: 'P001',
      startDate: '2024-01-01',
      endDate: '2024-01-31'
    })
    const rows = await result.getAll()
    
    // Known Excel result for this test data
    const excelCalculatedReward = 5000
    
    assert.strictEqual(rows[0].reward_amount, excelCalculatedReward)
    assert.strictEqual(rows[0].verification_status, 'verified')
  })
})