#!/usr/bin/env node
/**
 * ハイブリッド版: TypeScriptビジネスロジック + kuzu-wasm統合
 * TypeScriptで計算したプランをkuzu-wasmで検証・拡張
 */

import { createRequire } from 'module';
import { RewardModelService } from './reward-model-service.ts';

const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function verifyWithKuzu(plans) {
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);
  
  console.log('\n🔍 KuzuDBでの検証:\n');
  
  // プランデータをグラフDBに投入して関係性を分析
  const setupQuery = `
    CREATE NODE TABLE Plan(
      id STRING PRIMARY KEY,
      name STRING,
      profitMargin INT,
      riskLevel STRING
    );
    
    CREATE NODE TABLE Criterion(
      name STRING PRIMARY KEY,
      weight DOUBLE
    );
    
    CREATE REL TABLE EVALUATED_BY(
      FROM Plan TO Criterion,
      score DOUBLE
    );
  `;
  
  try {
    await conn.query(setupQuery);
    
    // プランをノードとして登録
    for (const plan of plans) {
      await conn.query(`
        CREATE (:Plan {
          id: '${plan.planId}',
          name: '${plan.planName}',
          profitMargin: ${plan.profitMargin},
          riskLevel: '${plan.riskLevel}'
        });
      `);
    }
    
    // 評価基準を登録
    await conn.query(`
      CREATE (:Criterion {name: '利益率', weight: 0.4});
      CREATE (:Criterion {name: 'リスク', weight: 0.3});
      CREATE (:Criterion {name: 'バランス', weight: 0.3});
    `);
    
    // 関係性を構築
    for (const plan of plans) {
      const profitScore = plan.profitMargin / 100;
      const riskScore = plan.riskLevel === 'low' ? 1.0 : 
                       plan.riskLevel === 'medium' ? 0.6 : 0.3;
      const balanceScore = 1 - Math.abs(0.5 - plan.profitMargin / 100) * 2;
      
      await conn.query(`
        MATCH (p:Plan {id: '${plan.planId}'}), (c:Criterion {name: '利益率'})
        CREATE (p)-[:EVALUATED_BY {score: ${profitScore}}]->(c);
      `);
      
      await conn.query(`
        MATCH (p:Plan {id: '${plan.planId}'}), (c:Criterion {name: 'リスク'})
        CREATE (p)-[:EVALUATED_BY {score: ${riskScore}}]->(c);
      `);
      
      await conn.query(`
        MATCH (p:Plan {id: '${plan.planId}'}), (c:Criterion {name: 'バランス'})
        CREATE (p)-[:EVALUATED_BY {score: ${balanceScore}}]->(c);
      `);
    }
    
    // 総合スコアを計算
    const result = await conn.query(`
      MATCH (p:Plan)-[e:EVALUATED_BY]->(c:Criterion)
      WITH p.name AS planName, 
           sum(e.score * c.weight) AS totalScore
      RETURN planName, CAST(totalScore * 100 AS INT) AS score
      ORDER BY score DESC;
    `);
    
    const scores = await result.getAllObjects();
    
    console.log('総合評価スコア（重み付け済み）:');
    scores.forEach((s, i) => {
      const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉';
      console.log(`  ${medal} ${s.planName}: ${s.score}点`);
    });
    
    await result.close();
  } catch (error) {
    console.error('Kuzu verification error:', error.message);
  }
  
  await conn.close();
  await db.close();
}

async function main() {
  console.log('💎 ハイブリッド版: TypeScript + KuzuDB\n');
  
  const input = {
    monthlyPrice: 20000,
    avgContractMonths: 24,
    maxCPA: 160000
  };
  
  // TypeScriptでプラン生成
  const plans = RewardModelService.generatePlans(input);
  
  console.log('📋 TypeScriptで生成されたプラン:');
  plans.forEach(plan => {
    console.log(`  - ${plan.planName}: 利益率${plan.profitMargin}%`);
  });
  
  // KuzuDBで検証と関係性分析
  await verifyWithKuzu(plans);
  
  console.log('\n✅ TypeScriptとKuzuDBの統合に成功しました！');
}

main().then(() => process.exit(0)).catch(err => {
  console.error(err);
  process.exit(1);
});