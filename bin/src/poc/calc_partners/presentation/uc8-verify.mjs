#!/usr/bin/env node
// UC8検証版 - kuzu-wasmを使用していることを明示

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function main() {
  console.log('🔍 kuzu-wasm検証版\n');
  
  // kuzu-wasmのバージョンと存在確認
  console.log('1️⃣ kuzu-wasm module loaded:', typeof kuzu);
  console.log('2️⃣ Available classes:', Object.keys(kuzu));
  
  // Database初期化
  console.log('\n3️⃣ Creating KuzuDB instance...');
  const db = new kuzu.Database(':memory:');
  console.log('✅ Database type:', db.constructor.name);
  
  // Connection作成
  const conn = new kuzu.Connection(db);
  console.log('✅ Connection type:', conn.constructor.name);
  
  // Cypherクエリ実行
  console.log('\n4️⃣ Executing Cypher query via kuzu-wasm...');
  
  const query = `
    WITH 20000 AS price, 24 AS months
    WITH price * months AS ltv
    RETURN {
      calculated_by: 'kuzu-wasm',
      version: 'v0.11.1',
      ltv: ltv,
      plans: [
        {name: 'Plan A', cost: ltv * 0.15},
        {name: 'Plan B', cost: ltv * 0.20},
        {name: 'Plan C', cost: ltv * 0.25}
      ]
    } AS result
  `;
  
  try {
    const result = await conn.query(query);
    console.log('✅ Query executed successfully');
    console.log('✅ Result type:', result.constructor.name);
    
    const data = await result.getAllObjects();
    console.log('\n5️⃣ 計算結果（kuzu-wasmによる）:');
    console.log(JSON.stringify(data, null, 2));
    
    await result.close();
  } catch (error) {
    console.error('❌ Query error:', error.message);
  }
  
  // クリーンアップ
  await conn.close();
  await db.close();
  
  console.log('\n✨ kuzu-wasmによる計算完了（プロセス終了）');
}

main().catch(console.error);