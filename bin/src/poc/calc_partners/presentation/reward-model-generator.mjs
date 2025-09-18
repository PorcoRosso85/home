#!/usr/bin/env node
// 報酬モデル・ジェネレーター - 3つの最適プランを自動生成

import { createRequire } from 'module';
import { REWARD_PLANS, DEFAULTS } from './variables.mjs';

const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function main() {
  console.log('💎 UC8: 報酬モデル・ジェネレーター（一点突破）\n');
  
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);

  // ========================================================================
  // 唯一のクエリ: 3つの報酬プランを自動生成
  // ========================================================================
  console.log('社長、以下の3つだけ教えてください：');
  console.log('- 月額単価: 20,000円');
  console.log('- 平均契約期間: 24ヶ月');
  console.log('- 許容CPA: 160,000円\n');
  
  // variables.mjsから取得したプラン定義を使用
  const plans = Object.values(REWARD_PLANS);
  
  const query = `
    WITH 20000 AS monthlyPrice, 
         24 AS avgContractMonths, 
         160000 AS maxCPA
    
    // LTV計算
    WITH monthlyPrice * avgContractMonths AS ltv, maxCPA
    
    // variables.mjsから取得したプラン定義を基に計算
    WITH ltv, maxCPA,
    [
      {
        name: '${plans[0].name}',
        description: '${plans[0].tagline}',
        structure: '${plans[0].structure}',
        cost: ltv * ${plans[0].formula.revenueShareRate} * ${plans[0].formula.durationMultiplier},
        reason: '${plans[0].bestFor}'
      },
      {
        name: '${plans[1].name}',
        description: '${plans[1].tagline}',
        structure: '${plans[1].structure}',
        cost: ${plans[1].formula.initialBonus} + ltv * ${plans[1].formula.revenueShareRate},
        reason: '${plans[1].bestFor}'
      },
      {
        name: '${plans[2].name}',
        description: '${plans[2].tagline}',
        structure: '${plans[2].structure}',
        cost: ltv * ${plans[2].formula.revenueShareRate},
        reason: '${plans[2].bestFor}'
      }
    ] AS plans
    
    UNWIND plans AS plan
    RETURN {
      planName: plan.name,
      description: plan.description,
      structure: plan.structure,
      partnerCost: CAST(plan.cost AS INT),
      yourProfit: CAST(ltv - plan.cost AS INT),
      profitMargin: CAST((ltv - plan.cost) * 100.0 / ltv AS INT),
      reason: plan.reason
    } AS recommendation
  `;

  try {
    const result = await conn.query(query);
    const plans = await result.getAllObjects();
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    console.log('🎯 あなたの会社に最適な3つのプラン:\n');
    
    plans.forEach((p, i) => {
      const plan = p.recommendation;
      console.log(`【プラン${i+1}】${plan.planName}`);
      console.log(`  ${plan.description}`);
      console.log(`  報酬体系: ${plan.structure}`);
      console.log(`  パートナーへの支払: ¥${plan.partnerCost.toLocaleString()}`);
      console.log(`  あなたの利益: ¥${plan.yourProfit.toLocaleString()}`);
      console.log(`  利益率: ${plan.profitMargin}%`);
      console.log(`  推奨理由: ${plan.reason}\n`);
    });
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    console.log('💬 「どのプランがお気に召しましたか？」');
    console.log('   「数値を調整したい場合は、その場で再計算します」\n');
    
    await result.close();
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await conn.close();
  await db.close();
}

main().then(() => process.exit(0)).catch(err => {
  console.error(err);
  process.exit(1);
});