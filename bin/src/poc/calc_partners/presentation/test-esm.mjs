#!/usr/bin/env node
// test-esm.mjs - Node.js ESMでkuzu-wasm動作確認

import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// CJSモジュールをESMから読み込み
const kuzu = require('kuzu-wasm/nodejs');

async function main() {
  console.log('🚀 Starting Kuzu WASM ESM Test...\n');
  
  try {
    // 1. Database初期化
    console.log('1. Initializing in-memory database...');
    const db = new kuzu.Database(':memory:', 1 << 28); // 256MB
    const conn = new kuzu.Connection(db, 1);
    console.log('✅ Database initialized\n');
    
    // 2. ハードコードされたクエリでテスト
    console.log('2. Testing simple query...');
    const simpleQuery = `
      WITH 20000 AS price, 24 AS duration, 160000 AS maxCPA
      WITH price * duration AS ltv, maxCPA
      RETURN {
        ltv: ltv,
        maxCPA: maxCPA,
        profitMargin: (ltv - maxCPA) * 1.0 / ltv
      } AS calculation
    `;
    
    const result = await conn.query(simpleQuery);
    const rows = await result.getAllObjects();  // 正しいメソッド
    console.log('Query Result:', JSON.stringify(rows, null, 2));
    console.log('✅ Query executed successfully\n');
    
    // 3. 報酬モデル生成のシミュレーション（簡易版）
    console.log('3. Testing reward model generation...');
    const modelQuery = `
      WITH 20000 AS price, 24 AS duration, 160000 AS cpa
      WITH price * duration AS ltv, cpa
      UNWIND [
        {name: 'Conservative', rate: 0.10, score: 0.0},
        {name: 'Standard', rate: 0.15, score: 0.0},
        {name: 'Aggressive', rate: 0.20, score: 0.0}
      ] AS model
      WITH model, ltv, cpa,
           ltv * model.rate AS cost,
           1.0 - model.rate AS margin
      WITH model.name AS plan,
           cost AS partnerCost,
           margin * 100 AS profitMargin,
           margin * 0.7 + 0.3 AS score
      RETURN plan, 
             CAST(partnerCost AS INT) AS cost, 
             CAST(profitMargin AS INT) AS margin
    `;
    
    const modelResult = await conn.query(modelQuery);
    const models = await modelResult.getAllObjects();
    console.log('Top 3 Models:');
    models.forEach((model, i) => {
      console.log(`  ${i+1}. ${model.plan}: Cost=¥${model.cost}, Margin=${model.margin}%`);
    });
    console.log('✅ Model generation successful\n');
    
    // 4. クリーンアップ
    await result.close();
    await modelResult.close();
    await conn.close();
    await db.close();
    
    console.log('✨ All tests passed! ESM + kuzu-wasm works in terminal.');
    
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

main();