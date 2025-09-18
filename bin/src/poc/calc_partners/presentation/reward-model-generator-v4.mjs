#!/usr/bin/env node
/**
 * 報酬モデル・ジェネレーター v4
 * infra層のkuzu実装を使用する版
 */

import { createRequire } from 'module';
import { REWARD_PLANS } from './variables.mjs';
import { validateUserParams, applyDefaults } from './user-params.mjs';
import { ENV_CONFIG } from './env-config.mjs';
import {
  calculatePlanCost,
  calculateProfit,
  calculateProfitMargin,
  calculateROI,
  evaluateProfitMargin,
  evaluateROI
} from './domain/reward-plans.mjs';

// infra層のkuzu実装をインポート（試験的）
import { initializeKuzuForTest, executeTestQuery } from '../infrastructure/kuzu.test.js';

async function generatePlansWithInfraKuzu(userParams) {
  // インフラ層のkuzu初期化を使用
  const { conn, close } = await initializeKuzuForTest();
  
  try {
    const params = applyDefaults(userParams);
    const plans = Object.values(REWARD_PLANS);
    const ltv = params.monthlyPrice * params.contractMonths;
    
    // 基本的なクエリテスト
    const testQuery = `
      WITH ${ltv} AS ltv, 
           ${params.monthlyPrice} AS monthlyPrice,
           ${params.contractMonths} AS contractMonths
      RETURN {
        ltv: ltv,
        monthlyRevenue: monthlyPrice,
        totalRevenue: ltv
      } AS result
    `;
    
    const testResults = await executeTestQuery(conn, testQuery);
    console.log('インフラ層kuzu動作確認:', testResults[0]);
    
    // プラン計算
    const enrichedPlans = plans.map(plan => {
      const cost = calculatePlanCost(plan.formula, ltv);
      const profit = calculateProfit(ltv, cost);
      const profitMargin = calculateProfitMargin(profit, ltv);
      const roi = calculateROI(profit, cost);
      
      return {
        planName: plan.name,
        description: plan.tagline,
        partnerCost: Math.round(cost),
        yourProfit: Math.round(profit),
        profitMargin,
        roi,
        evaluation: {
          profitMarginRating: evaluateProfitMargin(profitMargin, ENV_CONFIG.evaluation.profitMargin),
          roiRating: evaluateROI(roi, ENV_CONFIG.evaluation.roi)
        }
      };
    });
    
    return enrichedPlans;
  } finally {
    await close();
  }
}

async function main() {
  console.log('💎 UC8: 報酬モデル・ジェネレーター v4（infra層統合版）\n');
  
  const userInput = {
    monthlyPrice: 20000,
    contractMonths: 24,
    maxCPA: 160000
  };
  
  const validation = validateUserParams(userInput);
  if (!validation.valid) {
    console.error('入力エラー:', validation.errors);
    process.exit(1);
  }
  
  try {
    const plans = await generatePlansWithInfraKuzu(userInput);
    
    console.log('\n🎯 計算結果:\n');
    plans.forEach((plan, i) => {
      console.log(`【プラン${i+1}】${plan.planName}`);
      console.log(`  ${plan.description}`);
      console.log(`  パートナーコスト: ¥${plan.partnerCost.toLocaleString()}`);
      console.log(`  利益: ¥${plan.yourProfit.toLocaleString()}`);
      console.log(`  利益率: ${plan.profitMargin}% (${plan.evaluation.profitMarginRating})`);
      console.log(`  ROI: ${plan.roi}% (${plan.evaluation.roiRating})\n`);
    });
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error('\n❌ infra層のkuzu実装をpresentation層から使用できませんでした');
    console.error('理由: モジュール解決の問題またはTypeScript/JavaScript混在の問題');
    process.exit(1);
  }
}

main().then(() => process.exit(0)).catch(err => {
  console.error(err);
  process.exit(1);
});