#!/usr/bin/env -S npx tsx
/**
 * 報酬モデル・ジェネレーター（TypeScript版）
 * infra層のkuzu実装を使用
 */

import { REWARD_PLANS, ENV_CONFIG } from './variables';
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
  type PlanCalculationResult
} from './domain/reward-plans';

// infra層のkuzu実装をインポート
import { initializeKuzuForTest, executeTestQuery } from '../infrastructure/kuzu.test';

interface UserInput {
  monthlyPrice: number;
  contractMonths: number;
  maxCPA: number;
  expectedPartners?: number;
  simulationMonths?: number;
}

async function generatePlansWithKuzu(userInput: UserInput): Promise<PlanCalculationResult[]> {
  const { conn, close } = await initializeKuzuForTest();
  
  try {
    // デフォルト値を適用
    const params = {
      ...userInput,
      expectedPartners: userInput.expectedPartners ?? 5,
      simulationMonths: userInput.simulationMonths ?? 6
    };
    
    const plans = Object.values(REWARD_PLANS);
    const ltv = params.monthlyPrice * params.contractMonths;
    const monthlyRevenue = calculateMonthlyRevenue(params.expectedPartners, params.monthlyPrice);
    
    // Cypherクエリでデータ検証
    const validationQuery = `
      WITH ${ltv} AS ltv,
           ${params.monthlyPrice} AS monthlyPrice,
           ${params.contractMonths} AS contractMonths
      RETURN {
        ltv: ltv,
        monthlyRevenue: monthlyPrice,
        validation: ltv = monthlyPrice * contractMonths
      } AS result
    `;
    
    const validationResult = await executeTestQuery(conn, validationQuery);
    console.log('データ検証:', validationResult[0].result);
    
    // 各プランを計算
    const results: PlanCalculationResult[] = plans.map(plan => {
      const cost = calculatePlanCost(plan.formula, ltv);
      const profit = calculateProfit(ltv, cost);
      const profitMargin = calculateProfitMargin(profit, ltv);
      const roi = calculateROI(profit, cost);
      const paybackPeriod = calculatePaybackPeriod(cost, monthlyRevenue);
      
      const monthlyCost = calculateMonthlyCost(
        params.expectedPartners,
        cost,
        params.contractMonths
      );
      const monthlyProfit = monthlyRevenue - monthlyCost;
      
      return {
        planId: plan.id,
        planName: plan.name,
        description: plan.tagline,
        structure: plan.structure,
        riskLevel: plan.riskLevel,
        primaryReason: plan.primaryReason,
        partnerCost: Math.round(cost),
        yourProfit: Math.round(profit),
        profitMargin,
        roi,
        paybackPeriod,
        monthlyRevenue: Math.round(monthlyRevenue),
        monthlyCost: Math.round(monthlyCost),
        monthlyProfit: Math.round(monthlyProfit),
        pros: plan.pros,
        cons: plan.cons,
        riskFactors: plan.riskFactors,
        bestFor: plan.bestFor,
        evaluation: {
          profitMarginRating: evaluateProfitMargin(profitMargin, ENV_CONFIG.evaluation.profitMargin),
          roiRating: evaluateROI(roi, ENV_CONFIG.evaluation.roi)
        }
      };
    });
    
    return results;
  } finally {
    await close();
  }
}

function displayResults(plans: PlanCalculationResult[]): void {
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
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
  });
  
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('📊 月次シミュレーション:\n');
  
  plans.forEach(plan => {
    console.log(`【${plan.planName}】`);
    console.log(`  月間収益: ${ENV_CONFIG.currencySymbol}${plan.monthlyRevenue.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  月間コスト: ${ENV_CONFIG.currencySymbol}${plan.monthlyCost.toLocaleString(ENV_CONFIG.locale)}`);
    console.log(`  月間利益: ${ENV_CONFIG.currencySymbol}${plan.monthlyProfit.toLocaleString(ENV_CONFIG.locale)}\n`);
  });
}

async function main(): Promise<void> {
  console.log('💎 UC8: 報酬モデル・ジェネレーター（TypeScript + infra層統合版）\n');
  
  const userInput: UserInput = {
    monthlyPrice: 20000,
    contractMonths: 24,
    maxCPA: 160000,
    expectedPartners: 5,
    simulationMonths: 6
  };
  
  console.log('入力パラメータ:');
  console.log(`- 月額単価: ${ENV_CONFIG.currencySymbol}${userInput.monthlyPrice.toLocaleString(ENV_CONFIG.locale)}`);
  console.log(`- 平均契約期間: ${userInput.contractMonths}ヶ月`);
  console.log(`- 許容CPA: ${ENV_CONFIG.currencySymbol}${userInput.maxCPA.toLocaleString(ENV_CONFIG.locale)}`);
  console.log(`- 想定パートナー数: ${userInput.expectedPartners}社/月`);
  console.log(`- シミュレーション期間: ${userInput.simulationMonths}ヶ月`);
  
  try {
    const plans = await generatePlansWithKuzu(userInput);
    displayResults(plans);
    
    console.log('✅ infra層のkuzu実装を使用して正常に動作しました！');
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// 直接実行された場合のみmainを実行
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then(() => process.exit(0))
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}