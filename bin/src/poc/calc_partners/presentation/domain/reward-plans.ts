/**
 * 報酬プラン計算ドメインロジック（TypeScript版）
 * 純粋関数のみで構成（副作用なし）
 */

import type { RewardFormula } from '../variables';

/**
 * プランのコスト計算
 */
export function calculatePlanCost(formula: RewardFormula, ltv: number): number {
  return formula.initialBonus + 
         (ltv * formula.revenueShareRate * formula.durationMultiplier);
}

/**
 * 利益計算
 */
export function calculateProfit(ltv: number, cost: number): number {
  return ltv - cost;
}

/**
 * 利益率計算
 */
export function calculateProfitMargin(profit: number, ltv: number): number {
  if (ltv === 0) return 0;
  return Math.round((profit / ltv) * 100);
}

/**
 * ROI計算
 */
export function calculateROI(profit: number, cost: number): number {
  if (cost === 0) return 0;
  return Math.round((profit / cost) * 100);
}

/**
 * 投資回収期間計算
 */
export function calculatePaybackPeriod(cost: number, monthlyRevenue: number): number {
  if (monthlyRevenue === 0) return 0;
  return Math.round(cost / monthlyRevenue);
}

/**
 * 利益率の評価
 */
export function evaluateProfitMargin(
  margin: number, 
  criteria: { excellent: number; good: number; acceptable: number }
): 'excellent' | 'good' | 'acceptable' | 'poor' {
  if (margin >= criteria.excellent) return 'excellent';
  if (margin >= criteria.good) return 'good';
  if (margin >= criteria.acceptable) return 'acceptable';
  return 'poor';
}

/**
 * ROIの評価
 */
export function evaluateROI(
  roi: number,
  criteria: { excellent: number; good: number; acceptable: number }
): 'excellent' | 'good' | 'acceptable' | 'poor' {
  const roiDecimal = roi / 100;
  if (roiDecimal >= criteria.excellent) return 'excellent';
  if (roiDecimal >= criteria.good) return 'good';
  if (roiDecimal >= criteria.acceptable) return 'acceptable';
  return 'poor';
}

/**
 * 月次収益計算
 */
export function calculateMonthlyRevenue(partners: number, monthlyPrice: number): number {
  return partners * monthlyPrice;
}

/**
 * 月次コスト計算
 */
export function calculateMonthlyCost(
  partners: number, 
  planCost: number, 
  contractMonths: number
): number {
  if (contractMonths === 0) return 0;
  return partners * planCost / contractMonths;
}

/**
 * プラン計算結果の型定義
 */
export interface PlanCalculationResult {
  planId: string;
  planName: string;
  description: string;
  structure: string;
  riskLevel: 'low' | 'medium' | 'high';
  primaryReason: string;
  partnerCost: number;
  yourProfit: number;
  profitMargin: number;
  roi: number;
  paybackPeriod: number;
  monthlyRevenue: number;
  monthlyCost: number;
  monthlyProfit: number;
  pros: string[];
  cons: string[];
  riskFactors: string[];
  bestFor: string;
  evaluation: {
    profitMarginRating: 'excellent' | 'good' | 'acceptable' | 'poor';
    roiRating: 'excellent' | 'good' | 'acceptable' | 'poor';
  };
}