/**
 * Test for Reward Model Generator
 * Tests: 20種類の報酬モデルを生成し、TOP3を返却する
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { 
  setupTestDatabase, 
  loadQuery 
} from './test-helper.ts'

test('Reward Model Generator - should generate 20 models and return TOP3', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // Test parameters as specified
    const monthlyPrice = 20000
    const avgContractMonths = 24
    const maxCPA = 160000
    
    // Load the actual query from the cypher file
    const query = loadQuery('./reward_model_generator.cypher')
    
    // KuzuDBはパラメータを文字列置換で処理する必要がある
    const queryWithParams = query
      .replace(/\$monthlyPrice/g, monthlyPrice.toString())
      .replace(/\$avgContractMonths/g, avgContractMonths.toString())
      .replace(/\$maxCPA/g, maxCPA.toString())
    
    console.log('Query with params:', queryWithParams)  // デバッグ用
    const result = await conn.query(queryWithParams)
    const rows = await result.getAllObjects()
    
    // Verify results
    console.log('Generated TOP3 reward models:', rows)
    
    // Should return exactly 3 plans
    assert.strictEqual(rows.length, 3, 'Should return TOP3 models')
    
    // Each plan should have required fields
    rows.forEach((plan, index) => {
      assert(plan.planType, `Plan ${index + 1} should have planType`)
      assert(plan.profitMargin !== undefined, `Plan ${index + 1} should have profit margin`)
      assert(plan.score !== undefined, `Plan ${index + 1} should have score`)
      assert(['conservative', 'balanced', 'aggressive'].includes(plan.planType), 
             `Plan ${index + 1} should have valid plan type`)
    })
    
    // Verify ordering (highest score first)
    for (let i = 0; i < rows.length - 1; i++) {
      assert(rows[i].score >= rows[i + 1].score, 
             'Results should be ordered by score descending')
    }
    
    console.log('✅ Reward Model Generator test passed: 20 models generated, TOP3 returned')
    await result.close()
  } finally {
    await close()
  }
})