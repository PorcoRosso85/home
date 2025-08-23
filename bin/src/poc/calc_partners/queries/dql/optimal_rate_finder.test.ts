/**
 * Test for Optimal Rate Finder
 * Tests: Finding optimal reward rates that balance profit and partner satisfaction
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { 
  setupTestDatabase, 
  loadQuery
} from './test-helper.ts'

test('Optimal Rate Finder - should find optimal reward rates', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Test parameters
    const targetLtv = 500000  // 500K target LTV
    const minRate = 0.05      // 5% minimum rate
    const maxRate = 0.35      // 35% maximum rate
    const stepSize = 0.05     // 5% increments
    
    // Load and execute query
    const query = loadQuery('./optimal_rate_finder.cypher')
    const queryWithParams = query
      .replace(/\$targetLtv/g, targetLtv.toString())
      .replace(/\$minRate/g, minRate.toString())
      .replace(/\$maxRate/g, maxRate.toString())
      .replace(/\$stepSize/g, stepSize.toString())
    
    const result = await conn.query(queryWithParams)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Top optimal rates:', rows)
    
    // Should return top 5 rates
    assert(rows.length > 0 && rows.length <= 5, 'Should return top 5 optimal rates')
    
    // Each result should have required fields
    rows.forEach((row, index) => {
      assert(row.ratePercent !== undefined, `Row ${index} should have rate percent`)
      assert(row.totalCost !== undefined, `Row ${index} should have total cost`)
      assert(row.totalProfit !== undefined, `Row ${index} should have total profit`)
      assert(row.profitMarginPercent !== undefined, `Row ${index} should have profit margin`)
      assert(row.partnerSatisfaction !== undefined, `Row ${index} should have satisfaction score`)
      assert(row.score !== undefined, `Row ${index} should have optimization score`)
      assert(row.recommendation, `Row ${index} should have recommendation`)
    })
    
    // Results should be ordered by optimization score (descending)
    for (let i = 0; i < rows.length - 1; i++) {
      assert(rows[i].score >= rows[i + 1].score,
             'Results should be ordered by optimization score descending')
    }
    
    // Verify calculations
    rows.forEach(row => {
      // Total profit should be positive
      assert(row.totalProfit > 0, 'Total profit should be positive')
      
      // Profit margin should be reasonable (between 0 and 100)
      assert(row.profitMarginPercent >= 0 && row.profitMarginPercent <= 100,
             'Profit margin should be between 0 and 100')
      
      // Partner satisfaction should be between 0 and 100
      assert(row.partnerSatisfaction >= 0 && row.partnerSatisfaction <= 100,
             'Partner satisfaction should be between 0 and 100')
    })
    
    // The top result should have a balanced score
    const topResult = rows[0]
    console.log('Optimal rate recommendation:', {
      rate: `${topResult.ratePercent}%`,
      profitMargin: `${topResult.profitMarginPercent}%`,
      satisfaction: `${topResult.partnerSatisfaction}%`,
      recommendation: topResult.recommendation
    })
    
    console.log('✅ Optimal Rate Finder test passed: Found optimal rates successfully')
    await result.close()
  } finally {
    await close()
  }
})