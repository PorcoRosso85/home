/**
 * Test for UC1: Partner LTV Ranking
 * Business Value: Identify most profitable partners at a glance
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { createRequire } from 'module'
import { readFileSync } from 'fs'

const require = createRequire(import.meta.url)
const kuzu = require('kuzu-wasm/nodejs')

test('UC1: Partner LTV Ranking - should rank partners by total customer LTV', async () => {
  // Setup
  const db = new kuzu.Database(':memory:', 1 << 30)
  const conn = new kuzu.Connection(db, 4)
  
  // Create schema
  await conn.query(`
    CREATE NODE TABLE Partner(
      id INT64, name STRING, tier STRING, PRIMARY KEY (id)
    )
  `)
  await conn.query(`
    CREATE NODE TABLE Customer(
      id INT64, name STRING, ltv DOUBLE, source STRING, PRIMARY KEY (id)
    )
  `)
  await conn.query(`
    CREATE NODE TABLE Subscription(
      id INT64, customer_id INT64, monthlyFee DOUBLE, duration INT32, PRIMARY KEY (id)
    )
  `)
  await conn.query(`
    CREATE REL TABLE INTRODUCED(FROM Partner TO Customer)
  `)
  await conn.query(`
    CREATE REL TABLE HAS_SUBSCRIPTION(FROM Customer TO Subscription)
  `)
  
  // Insert test data
  await conn.query(`CREATE (p:Partner {id: 1, name: 'Partner A', tier: 'Gold'})`)
  await conn.query(`CREATE (p:Partner {id: 2, name: 'Partner B', tier: 'Silver'})`)
  await conn.query(`CREATE (c:Customer {id: 1, name: 'Customer 1', ltv: 50000})`)
  await conn.query(`CREATE (c:Customer {id: 2, name: 'Customer 2', ltv: 30000})`)
  await conn.query(`CREATE (c:Customer {id: 3, name: 'Customer 3', ltv: 20000})`)
  await conn.query(`CREATE (s:Subscription {id: 1, customer_id: 1, monthlyFee: 2000, duration: 25})`)
  await conn.query(`CREATE (s:Subscription {id: 2, customer_id: 2, monthlyFee: 1500, duration: 20})`)
  await conn.query(`CREATE (s:Subscription {id: 3, customer_id: 3, monthlyFee: 1000, duration: 20})`)
  
  // Create relationships
  await conn.query(`MATCH (p:Partner {id: 1}), (c:Customer {id: 1}) CREATE (p)-[:INTRODUCED]->(c)`)
  await conn.query(`MATCH (p:Partner {id: 1}), (c:Customer {id: 2}) CREATE (p)-[:INTRODUCED]->(c)`)
  await conn.query(`MATCH (p:Partner {id: 2}), (c:Customer {id: 3}) CREATE (p)-[:INTRODUCED]->(c)`)
  await conn.query(`MATCH (c:Customer {id: 1}), (s:Subscription {id: 1}) CREATE (c)-[:HAS_SUBSCRIPTION]->(s)`)
  await conn.query(`MATCH (c:Customer {id: 2}), (s:Subscription {id: 2}) CREATE (c)-[:HAS_SUBSCRIPTION]->(s)`)
  await conn.query(`MATCH (c:Customer {id: 3}), (s:Subscription {id: 3}) CREATE (c)-[:HAS_SUBSCRIPTION]->(s)`)
  
  // Read and execute query
  const queryContent = readFileSync('./uc1_partner_ltv_ranking.cypher', 'utf-8')
  const query = queryContent.split('\n')
    .filter(line => !line.trim().startsWith('//') && !line.trim().startsWith('--') && line.trim())
    .filter(line => !line.includes('┌') && !line.includes('│') && !line.includes('└'))
    .join(' ')
    .replace(/;.*$/, '')
  
  const result = await conn.query(query)
  const rows = await result.getAllObjects()
  
  // Verify results
  console.log('Query result columns:', Object.keys(rows[0] || {}))
  console.log('First row:', rows[0])
  
  assert.strictEqual(rows.length, 2, 'Should have 2 partners')
  // Use the actual column names from the query
  assert.strictEqual(rows[0].partner_name || rows[0]['p.name'], 'Partner A', 'Partner A should be first')
  assert.strictEqual(Number(rows[0].total_ltv), 80000, 'Partner A total LTV should be 80000')
  assert.strictEqual(rows[1].partner_name || rows[1]['p.name'], 'Partner B', 'Partner B should be second')
  assert.strictEqual(Number(rows[1].total_ltv), 20000, 'Partner B total LTV should be 20000')
  
  // Cleanup
  await result.close()
  await conn.close()
  await db.close()
  await kuzu.close()
  
  console.log('✅ UC1 test passed: Partners ranked by LTV correctly')
})