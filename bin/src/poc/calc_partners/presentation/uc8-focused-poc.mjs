#!/usr/bin/env node
// UC8専用POC - 「報酬モデル・ジェネレーター」のみ

import { createRequire } from 'module';
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
  
  // ハードコードされた「専門家の初期提案」
  const query = `
    WITH 20000 AS monthlyPrice, 
         24 AS avgContractMonths, 
         160000 AS maxCPA
    
    // LTV計算
    WITH monthlyPrice * avgContractMonths AS ltv, maxCPA
    
    // 専門家として提案する3つのプラン（ハードコード = プロの意見）
    WITH ltv, maxCPA,
    [
      {
        name: '手堅く始める',
        description: 'リスクを最小限に、成果が出た分だけ支払い',
        structure: '売上の15%を12ヶ月間',
        cost: ltv * 0.15 * 0.5,  // 12ヶ月/24ヶ月 = 0.5
        reason: '初めてのパートナープログラムに最適'
      },
      {
        name: '有力パートナー向け',
        description: '初期インセンティブ＋継続報酬のバランス型',
        structure: '初期3万円＋売上の10%永続',
        cost: 30000 + ltv * 0.10,
        reason: '実績のあるパートナーを引き付ける'
      },
      {
        name: '市場支配を狙う',
        description: '報酬率を高めに設定し、急速拡大',
        structure: '月間紹介数に応じて15-35%の階層報酬',
        cost: ltv * 0.25,  // 平均25%で計算
        reason: '競合からパートナーを奪い取る'
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

main();