#!/usr/bin/env node
/**
 * 報酬モデル・ジェネレーター v2
 * データ構造を適切に分類した改良版
 */

import { createRequire } from 'module';
import { REWARD_PLANS, DEFAULTS } from './variables.mjs';
import { USER_PARAMS_SCHEMA, validateUserParams, applyDefaults } from './user-params.mjs';
import { ENV_CONFIG } from './env-config.mjs';

const require = createRequire(import.meta.url);
const kuzu = require('kuzu-wasm/nodejs');

async function generatePlansWithSimulation(userParams) {
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);
  
  // デフォルト値を適用
  const params = applyDefaults(userParams);
  const plans = Object.values(REWARD_PLANS);
  
  // LTV計算
  const ltv = params.monthlyPrice * params.contractMonths;
  
  // 拡張クエリ: ROIと時系列シミュレーションを追加
  const query = `
    WITH ${params.monthlyPrice} AS monthlyPrice, 
         ${params.contractMonths} AS contractMonths, 
         ${params.maxCPA} AS maxCPA,
         ${params.expectedPartners} AS expectedPartners,
         ${params.simulationMonths} AS simulationMonths
    
    // LTV計算
    WITH monthlyPrice * contractMonths AS ltv, maxCPA, expectedPartners, simulationMonths
    
    // プラン定義を基に計算（ROI追加）
    WITH ltv, maxCPA, expectedPartners, simulationMonths,
    [
      {
        id: '${plans[0].id}',
        name: '${plans[0].name}',
        description: '${plans[0].tagline}',
        structure: '${plans[0].structure}',
        cost: ltv * ${plans[0].formula.revenueShareRate} * ${plans[0].formula.durationMultiplier},
        riskLevel: '${plans[0].riskLevel}',
        primaryReason: '${plans[0].primaryReason}'
      },
      {
        id: '${plans[1].id}',
        name: '${plans[1].name}',
        description: '${plans[1].tagline}',
        structure: '${plans[1].structure}',
        cost: ${plans[1].formula.initialBonus} + ltv * ${plans[1].formula.revenueShareRate},
        riskLevel: '${plans[1].riskLevel}',
        primaryReason: '${plans[1].primaryReason}'
      },
      {
        id: '${plans[2].id}',
        name: '${plans[2].name}',
        description: '${plans[2].tagline}',
        structure: '${plans[2].structure}',
        cost: ltv * ${plans[2].formula.revenueShareRate},
        riskLevel: '${plans[2].riskLevel}',
        primaryReason: '${plans[2].primaryReason}'
      }
    ] AS plans
    
    UNWIND plans AS plan
    WITH plan, ltv, expectedPartners, simulationMonths
    RETURN {
      // 基本情報
      planId: plan.id,
      planName: plan.name,
      description: plan.description,
      structure: plan.structure,
      riskLevel: plan.riskLevel,
      primaryReason: plan.primaryReason,
      
      // 財務インパクト
      partnerCost: CAST(plan.cost AS INT),
      yourProfit: CAST(ltv - plan.cost AS INT),
      profitMargin: CAST((ltv - plan.cost) * 100.0 / ltv AS INT),
      roi: CAST((ltv - plan.cost) * 100.0 / plan.cost AS INT),
      paybackPeriod: CASE 
        WHEN plan.cost = 0 THEN 0
        ELSE CAST(plan.cost / (ltv / ${params.contractMonths}) AS INT)
      END,
      
      // 月次シミュレーション（簡易版）
      monthlyRevenue: CAST(expectedPartners * ${params.monthlyPrice} AS INT),
      monthlyCost: CAST(expectedPartners * plan.cost / ${params.contractMonths} AS INT),
      monthlyProfit: CAST(expectedPartners * (ltv - plan.cost) / ${params.contractMonths} AS INT),
      
      // 期間合計
      totalRevenue: CAST(expectedPartners * ltv * simulationMonths / ${params.contractMonths} AS INT),
      totalCost: CAST(expectedPartners * plan.cost * simulationMonths / ${params.contractMonths} AS INT),
      totalProfit: CAST(expectedPartners * (ltv - plan.cost) * simulationMonths / ${params.contractMonths} AS INT)
    } AS result
  `;

  try {
    const result = await conn.query(query);
    const plansData = await result.getAllObjects();
    await result.close();
    
    // プランごとの詳細情報を追加
    const enrichedPlans = plansData.map(p => {
      const plan = REWARD_PLANS[p.result.planId];
      return {
        ...p.result,
        pros: plan.pros,
        cons: plan.cons,
        riskFactors: plan.riskFactors,
        bestFor: plan.bestFor,
        evaluation: evaluatePlan(p.result)
      };
    });
    
    return enrichedPlans;
  } finally {
    await conn.close();
    await db.close();
  }
}

function evaluatePlan(plan) {
  const { evaluation } = ENV_CONFIG;
  
  // 利益率評価
  let profitMarginRating = 'poor';
  if (plan.profitMargin >= evaluation.profitMargin.excellent) profitMarginRating = 'excellent';
  else if (plan.profitMargin >= evaluation.profitMargin.good) profitMarginRating = 'good';
  else if (plan.profitMargin >= evaluation.profitMargin.acceptable) profitMarginRating = 'acceptable';
  
  // ROI評価
  let roiRating = 'poor';
  const roiDecimal = plan.roi / 100;
  if (roiDecimal >= evaluation.roi.excellent) roiRating = 'excellent';
  else if (roiDecimal >= evaluation.roi.good) roiRating = 'good';
  else if (roiDecimal >= evaluation.roi.acceptable) roiRating = 'acceptable';
  
  return { profitMarginRating, roiRating };
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
  console.log('💎 UC8: 報酬モデル・ジェネレーター v2（データ構造改良版）\n');
  
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
    const plans = await generatePlansWithSimulation(userInput);
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