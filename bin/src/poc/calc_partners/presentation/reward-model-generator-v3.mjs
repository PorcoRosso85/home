#!/usr/bin/env node
/**
 * 報酬モデル・ジェネレーター v3
 * ドメインロジックを分離した改良版
 */

import { createRequire } from 'module';
import { REWARD_PLANS } from './variables.mjs';
import { USER_PARAMS_SCHEMA, validateUserParams, applyDefaults } from './user-params.mjs';
import { ENV_CONFIG } from './env-config.mjs';
import {
  calculatePlanCost,
  calculateProfit,
  calculateProfitMargin,
  calculateROI,
  calculatePaybackPeriod,
  evaluateProfitMargin,
  evaluateROI,
  calculateMonthlyRevenue,
  calculateMonthlyCost,
  calculateMonthlyProfit,
  calculateTotalRevenue,
  calculateTotalCost
} from './domain/reward-plans.mjs';

const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function generatePlansWithKuzu(userParams) {
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);
  
  // デフォルト値を適用
  const params = applyDefaults(userParams);
  const plans = Object.values(REWARD_PLANS);
  
  // LTV計算（ドメインロジックではなくここで計算）
  const ltv = params.monthlyPrice * params.contractMonths;
  const monthlyRevenue = calculateMonthlyRevenue(params.expectedPartners, params.monthlyPrice);
  
  // Cypherクエリで基本データを生成
  const query = `
    WITH ${ltv} AS ltv
    UNWIND [
      {id: '${plans[0].id}', formula: {
        revenueShareRate: ${plans[0].formula.revenueShareRate},
        durationMultiplier: ${plans[0].formula.durationMultiplier},
        initialBonus: ${plans[0].formula.initialBonus}
      }},
      {id: '${plans[1].id}', formula: {
        revenueShareRate: ${plans[1].formula.revenueShareRate},
        durationMultiplier: ${plans[1].formula.durationMultiplier},
        initialBonus: ${plans[1].formula.initialBonus}
      }},
      {id: '${plans[2].id}', formula: {
        revenueShareRate: ${plans[2].formula.revenueShareRate},
        durationMultiplier: ${plans[2].formula.durationMultiplier},
        initialBonus: ${plans[2].formula.initialBonus}
      }}
    ] AS plan
    RETURN plan.id AS planId, plan.formula AS formula, ltv
  `;
  
  try {
    const result = await conn.query(query);
    const plansData = await result.getAllObjects();
    await result.close();
    
    // ドメインロジックを使用して各プランを計算
    const enrichedPlans = plansData.map(data => {
      const plan = REWARD_PLANS[data.planId];
      
      // ドメインロジックで計算
      const cost = calculatePlanCost(data.formula, data.ltv);
      const profit = calculateProfit(data.ltv, cost);
      const profitMargin = calculateProfitMargin(profit, data.ltv);
      const roi = calculateROI(profit, cost);
      const paybackPeriod = calculatePaybackPeriod(cost, monthlyRevenue);
      
      // 月次計算
      const monthlyCost = calculateMonthlyCost(
        params.expectedPartners, 
        cost, 
        params.contractMonths
      );
      const monthlyProfit = calculateMonthlyProfit(monthlyRevenue, monthlyCost);
      
      // 期間合計
      const totalRevenue = calculateTotalRevenue(monthlyRevenue, params.simulationMonths);
      const totalCost = calculateTotalCost(monthlyCost, params.simulationMonths);
      const totalProfit = totalRevenue - totalCost;
      
      // 評価
      const profitMarginRating = evaluateProfitMargin(profitMargin, ENV_CONFIG.evaluation.profitMargin);
      const roiRating = evaluateROI(roi, ENV_CONFIG.evaluation.roi);
      
      return {
        // 基本情報
        planId: plan.id,
        planName: plan.name,
        description: plan.tagline,
        structure: plan.structure,
        riskLevel: plan.riskLevel,
        primaryReason: plan.primaryReason,
        
        // 財務インパクト
        partnerCost: Math.round(cost),
        yourProfit: Math.round(profit),
        profitMargin,
        roi,
        paybackPeriod,
        
        // 月次シミュレーション
        monthlyRevenue: Math.round(monthlyRevenue),
        monthlyCost: Math.round(monthlyCost),
        monthlyProfit: Math.round(monthlyProfit),
        
        // 期間合計
        totalRevenue: Math.round(totalRevenue),
        totalCost: Math.round(totalCost),
        totalProfit: Math.round(totalProfit),
        
        // メタ情報
        pros: plan.pros,
        cons: plan.cons,
        riskFactors: plan.riskFactors,
        bestFor: plan.bestFor,
        evaluation: { profitMarginRating, roiRating }
      };
    });
    
    return enrichedPlans;
  } finally {
    await conn.close();
    await db.close();
  }
}

function displayResults(plans) {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('🎯 あなたの会社に最適な3つのプラン:\n');
  
  plans.forEach((plan, i) => {
    const emoji = plan.evaluation.profitMarginRating === 'excellent' ? '⭐' : 
                  plan.evaluation.profitMarginRating === 'good' ? '👍' : 
                  plan.evaluation.profitMarginRating === 'acceptable' ? '✅' : '⚠️';
    
    console.log(`【プラン${i+1}】${plan.planName} ${emoji}`);
    console.log(`  ${plan.description}`);
    console.log(`  主な理由: ${plan.primaryReason}`);
    console.log(`  報酬体系: ${plan.structure}`);
    console.log(`  リスクレベル: ${plan.riskLevel}`);
    console.log(`  パートナーへの支払: ${ENV_CONFIG.currencySymbol}${plan.partnerCost.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  あなたの利益: ${ENV_CONFIG.currencySymbol}${plan.yourProfit.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  利益率: ${plan.profitMargin}% (${plan.evaluation.profitMarginRating})`);
    console.log(`  ROI: ${plan.roi}% (${plan.evaluation.roiRating})`);
    console.log(`  投資回収期間: ${plan.paybackPeriod}ヶ月`);
    console.log(`  推奨シーン: ${plan.bestFor}\n`);
    
    // pros/cons表示
    console.log(`  メリット:`);
    plan.pros.forEach(pro => console.log(`    ✓ ${pro}`));
    console.log(`  デメリット:`);
    plan.cons.forEach(con => console.log(`    ✗ ${con}`));
    console.log(`  リスク要因:`);
    plan.riskFactors.forEach(risk => console.log(`    ⚠ ${risk}`));
    console.log('');
  });
  
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('📊 シミュレーション結果（月次）:\n');
  
  plans.forEach(plan => {
    console.log(`【${plan.planName}】`);
    console.log(`  月間収益: ${ENV_CONFIG.currencySymbol}${plan.monthlyRevenue.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  月間コスト: ${ENV_CONFIG.currencySymbol}${plan.monthlyCost.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  月間利益: ${ENV_CONFIG.currencySymbol}${plan.monthlyProfit.toLocaleString(ENV_CONFIG.locale)}\n`);
  });
  
  console.log('💬 「どのプランがお気に召しましたか？」');
  console.log('   「数値を調整したい場合は、その場で再計算します」\n');
}

async function main() {
  console.log('💎 UC8: 報酬モデル・ジェネレーター v3（ドメイン分離版）\n');
  
  // ユーザー入力（実際はCLI引数やWeb UIから取得）
  const userInput = {
    monthlyPrice: 20000,
    contractMonths: 24,
    maxCPA: 160000,
    expectedPartners: 5,
    simulationMonths: 6
  };
  
  console.log('社長、以下の情報を入力いただきました：');
  console.log(`- 月額単価: ${ENV_CONFIG.currencySymbol}${userInput.monthlyPrice.toLocaleString(ENV_CONFIG.locale)}`);
  console.log(`- 平均契約期間: ${userInput.contractMonths}ヶ月`);
  console.log(`- 許容CPA: ${ENV_CONFIG.currencySymbol}${userInput.maxCPA.toLocaleString(ENV_CONFIG.locale)}`);
  console.log(`- 想定パートナー数: ${userInput.expectedPartners}社/月`);
  console.log(`- シミュレーション期間: ${userInput.simulationMonths}ヶ月\n`);
  
  // バリデーション
  const validation = validateUserParams(userInput);
  if (!validation.valid) {
    console.error('入力エラー:', validation.errors);
    process.exit(1);
  }
  
  try {
    const plans = await generatePlansWithKuzu(userInput);
    displayResults(plans);
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

main().then(() => process.exit(0)).catch(err => {
  console.error(err);
  process.exit(1);
});