#!/usr/bin/env node
// UC8 簡略版POC - 2つのクエリ結果を確認

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function main() {
  console.log('🚀 UC8 POC - 報酬モデル生成');
  
  const db = new kuzu.Database(':memory:', 1 << 28);
  const conn = new kuzu.Connection(db, 1);

  // ========================================================================
  // Query 1: シンプルな報酬モデル生成（TOP3）
  // ========================================================================
  console.log('\n📊 Query 1: TOP3報酬モデル');
  
  const query1 = `
    WITH 20000 AS price, 24 AS duration, 160000 AS maxCPA
    WITH price * duration AS ltv, maxCPA
    UNWIND [
      {name: 'Conservative', type: 'revenue', rate: 0.10},
      {name: 'Standard', type: 'revenue', rate: 0.15},
      {name: 'Aggressive', type: 'revenue', rate: 0.20},
      {name: 'Hybrid Low', type: 'hybrid', upfront: 30000, rate: 0.08},
      {name: 'Hybrid High', type: 'hybrid', upfront: 50000, rate: 0.10}
    ] AS model
    WITH model, ltv, maxCPA,
      CASE model.type
        WHEN 'revenue' THEN ltv * model.rate
        WHEN 'hybrid' THEN model.upfront + ltv * model.rate
      END AS cost
    WITH model.name AS planName,
         model.type AS planType,
         CAST(cost AS INT) AS partnerCost,
         CAST((1.0 - cost/ltv) * 100 AS INT) AS profitMargin
    LIMIT 3
    RETURN planName, planType, partnerCost, profitMargin
  `;

  const result1 = await conn.query(query1);
  const models = await result1.getAllObjects();
  
  console.log('\n✅ 期待する結果（ブラウザUIのカード表示用）:');
  console.log(JSON.stringify(models, null, 2));

  // ========================================================================
  // Query 2: シンプルなキャッシュフロー（3ヶ月分）
  // ========================================================================
  console.log('\n📈 Query 2: キャッシュフロー予測');
  
  const query2 = `
    WITH 30000 AS bonus, 0.10 AS rate, 5 AS volume
    UNWIND [1, 2, 3] AS month
    WITH month, 
         volume * bonus AS upfront,
         volume * 20000 * rate AS revShare,
         volume * 20000 AS revenue
    RETURN month, upfront, revShare, revenue,
           revenue - (upfront + revShare) AS profit
  `;

  const result2 = await conn.query(query2);
  const cashflow = await result2.getAllObjects();
  
  console.log('\n✅ 期待する結果（グラフ表示用）:');
  console.log(JSON.stringify(cashflow, null, 2));

  // クリーンアップ
  await result1.close();
  await result2.close();
  await conn.close();
  await db.close();

  console.log('\n✨ POC完了！これらのデータ構造をブラウザUIで使用します。');
}

main().catch(console.error);