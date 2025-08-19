/**
 * Simple test for ping.cypher - Minimal Node.js test
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)
const kuzu = require('kuzu-wasm/nodejs')

test('ping simple test', async () => {
  // Initialize
  await kuzu.init()
  
  // Create database and connection
  const db = new kuzu.Database(':memory:', 1 << 30)
  const conn = new kuzu.Connection(db, 4)
  
  // Run ping query
  const result = await conn.query("RETURN 'pong' AS response, 1 AS status")
  const rows = await result.getAllObjects()
  
  // Verify
  assert.strictEqual(rows.length, 1)
  assert.strictEqual(rows[0].response, 'pong')
  assert.strictEqual(Number(rows[0].status), 1)
  
  // Cleanup
  await result.close()
  await conn.close()
  await db.close()
  
  console.log('✅ Test passed!')
})