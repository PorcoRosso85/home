/**
 * Test-specific Kuzu WASM infrastructure for Node.js
 * 
 * Purpose: Enable fast Cypher query testing in Node.js environment
 * without browser dependencies
 */

import { createRequire } from 'module'
const require = createRequire(import.meta.url)
const kuzu = require('kuzu-wasm/nodejs')

export type TestKuzuConnection = {
  db: unknown
  conn: unknown
  close: () => Promise<void>
}

/**
 * Initialize Kuzu for testing in Node.js
 */
export const initializeKuzuForTest = async (): Promise<TestKuzuConnection> => {
  // Initialize kuzu module first
  await kuzu.init()
  
  // In-memory database with 1GB allocation
  const db = new kuzu.Database(':memory:', 1 << 30)
  // Connection with 4 threads
  const conn = new kuzu.Connection(db, 4)
  
  return {
    db,
    conn,
    close: async () => {
      await conn.close()
      await db.close()
    }
  }
}

/**
 * Execute Cypher query in test environment
 */
export const executeTestQuery = async (conn: any, query: string): Promise<any[]> => {
  const result = await conn.query(query)
  const rows = await result.getAllObjects()
  await result.close()
  return rows
}

/**
 * Setup database schema from DDL
 */
export const setupTestDatabase = async (conn: any, ddlQueries: string[]): Promise<void> => {
  for (const query of ddlQueries) {
    if (query.trim()) {
      const result = await conn.query(query)
      await result.close()
    }
  }
}

/**
 * Insert test data
 */
export const insertTestData = async (conn: any, data: {
  partners?: any[]
  transactions?: any[]
  rewards?: any[]
  rules?: any[]
}): Promise<void> => {
  // Insert Partners
  if (data.partners) {
    for (const partner of data.partners) {
      const query = `
        CREATE (p:Partner {
          id: $id,
          code: $code,
          name: $name,
          tier: $tier
        })
      `
      const result = await conn.query(query, partner)
      await result.close()
    }
  }
  
  // Insert Transactions
  if (data.transactions) {
    for (const transaction of data.transactions) {
      const query = `
        CREATE (t:Transaction {
          id: $id,
          partner_id: $partner_id,
          amount: $amount,
          status: $status,
          transaction_date: $transaction_date
        })
      `
      const result = await conn.query(query, transaction)
      await result.close()
    }
  }
  
  // Additional data types can be added as needed
}