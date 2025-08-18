/**
 * Test for ping.cypher - Database Connectivity Test
 * Pain Point: KuzuDBLa��h�Df�K~Zo��W_D
 */

import { describe, test, before, after } from 'node:test'
import assert from 'node:assert'
import { loadQuery } from '../../infrastructure/cypherLoader.ts'
import { getConnection } from '../../infrastructure/db.ts'
import type { KuzuDatabase } from 'kuzu-wasm'

describe('ping.cypher - Database Connectivity Test', () => {
  let conn: Database
  
  before(async () => {
    conn = await getConnection()
  })
  
  after(async () => {
    if (conn) {
      await conn.close()
    }
  })
  
  test('should return pong response without parameters', async () => {
    // Load query via cypherLoader
    const queryResult = await loadQuery('dql', 'ping')
    assert.strictEqual(queryResult.success, true)
    assert.ok(queryResult.data?.includes('pong'))
    
    // Execute query
    const result = await conn.query(queryResult.data!)
    const rows = await result.getAll()
    
    // Verify basic connectivity
    assert.strictEqual(rows.length, 1)
    assert.strictEqual(rows[0].response, 'pong')
    assert.strictEqual(rows[0].status, 1)
    assert.strictEqual(rows[0].database_type, 'KuzuDB')
    assert.strictEqual(rows[0].health_status, 'healthy')
  })
  
  test('should include statistics when requested', async () => {
    const queryResult = await loadQuery('dql', 'ping')
    
    // Execute with includeStats parameter
    const result = await conn.query(queryResult.data!, {
      includeStats: true
    })
    const rows = await result.getAll()
    
    // Verify statistics are included
    assert.ok(rows[0].statistics !== undefined)
    assert.ok('partners' in rows[0].statistics)
    assert.ok('transactions' in rows[0].statistics)
    assert.ok('rewards' in rows[0].statistics)
    assert.ok('rules' in rows[0].statistics)
    assert.ok('total_nodes' in rows[0].statistics)
  })
  
  test('should accept custom message parameter', async () => {
    const queryResult = await loadQuery('dql', 'ping')
    const customMessage = 'Production health check'
    
    // Execute with custom message
    const result = await conn.query(queryResult.data!, {
      customMessage: customMessage
    })
    const rows = await result.getAll()
    
    // Verify custom message is returned
    assert.strictEqual(rows[0].message, customMessage)
  })
  
  test('should handle timeout parameter gracefully', async () => {
    const queryResult = await loadQuery('dql', 'ping')
    
    // Execute with timeout parameter
    const result = await conn.query(queryResult.data!, {
      timeout: 10
    })
    const rows = await result.getAll()
    
    // Query should complete within timeout
    assert.strictEqual(rows.length, 1)
    assert.strictEqual(rows[0].response, 'pong')
  })
  
  test('should validate parameter types', async () => {
    const queryResult = await loadQuery('dql', 'ping')
    
    // Test with various parameter combinations
    const testCases = [
      { includeStats: false, expected: { hasStats: false } },
      { includeStats: true, expected: { hasStats: true } },
      { customMessage: '', expected: { message: 'Database connectivity test' } }, // Default when empty
      { customMessage: '�,��û��', expected: { message: '�,��û��' } }
    ]
    
    for (const testCase of testCases) {
      const result = await conn.query(queryResult.data!, testCase)
      const rows = await result.getAll()
      
      if ('hasStats' in testCase.expected) {
        const hasStats = rows[0].statistics !== null
        assert.strictEqual(hasStats, testCase.expected.hasStats)
      }
      
      if ('message' in testCase.expected) {
        assert.strictEqual(rows[0].message, testCase.expected.message)
      }
    }
  })
})