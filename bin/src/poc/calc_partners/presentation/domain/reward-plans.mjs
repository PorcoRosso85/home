/**
 * 報酬プラン計算ドメインロジック
 * 純粋関数のみで構成（副作用なし）
 */

/**
 * プランのコスト計算
 * @param {Object} formula - 計算式定義
 * @param {number} ltv - 顧客生涯価値
 * @returns {number} パートナーコスト
 */
export function calculatePlanCost(formula, ltv) {
  return formula.initialBonus + 
         (ltv * formula.revenueShareRate * formula.durationMultiplier);
}

/**
 * 利益計算
 * @param {number} ltv - 顧客生涯価値
 * @param {number} cost - パートナーコスト
 * @returns {number} 利益額
 */
export function calculateProfit(ltv, cost) {
  return ltv - cost;
}

/**
 * 利益率計算
 * @param {number} profit - 利益額
 * @param {number} ltv - 顧客生涯価値
 * @returns {number} 利益率（%）
 */
export function calculateProfitMargin(profit, ltv) {
  if (ltv === 0) return 0;
  return Math.round((profit / ltv) * 100);
}

/**
 * ROI計算
 * @param {number} profit - 利益額
 * @param {number} cost - 投資額
 * @returns {number} ROI（%）
 */
export function calculateROI(profit, cost) {
  if (cost === 0) return 0;
  return Math.round((profit / cost) * 100);
}

/**
 * 投資回収期間計算
 * @param {number} cost - パートナーコスト
 * @param {number} monthlyRevenue - 月間収益
 * @returns {number} 回収期間（月）
 */
export function calculatePaybackPeriod(cost, monthlyRevenue) {
  if (monthlyRevenue === 0) return 0;
  return Math.round(cost / monthlyRevenue);
}

/**
 * 利益率の評価
 * @param {number} margin - 利益率
 * @param {Object} criteria - 評価基準
 * @returns {string} 評価レベル
 */
export function evaluateProfitMargin(margin, criteria) {
  if (margin >= criteria.excellent) return 'excellent';
  if (margin >= criteria.good) return 'good';
  if (margin >= criteria.acceptable) return 'acceptable';
  return 'poor';
}

/**
 * ROIの評価
 * @param {number} roi - ROI（%）
 * @param {Object} criteria - 評価基準
 * @returns {string} 評価レベル
 */
export function evaluateROI(roi, criteria) {
  const roiDecimal = roi / 100;
  if (roiDecimal >= criteria.excellent) return 'excellent';
  if (roiDecimal >= criteria.good) return 'good';
  if (roiDecimal >= criteria.acceptable) return 'acceptable';
  return 'poor';
}

/**
 * 月次収益計算
 * @param {number} partners - パートナー数
 * @param {number} monthlyPrice - 月額単価
 * @returns {number} 月間収益
 */
export function calculateMonthlyRevenue(partners, monthlyPrice) {
  return partners * monthlyPrice;
}

/**
 * 月次コスト計算
 * @param {number} partners - パートナー数
 * @param {number} planCost - プランコスト
 * @param {number} contractMonths - 契約期間
 * @returns {number} 月間コスト
 */
export function calculateMonthlyCost(partners, planCost, contractMonths) {
  if (contractMonths === 0) return 0;
  return partners * planCost / contractMonths;
}

/**
 * 月次利益計算
 * @param {number} monthlyRevenue - 月間収益
 * @param {number} monthlyCost - 月間コスト
 * @returns {number} 月間利益
 */
export function calculateMonthlyProfit(monthlyRevenue, monthlyCost) {
  return monthlyRevenue - monthlyCost;
}

/**
 * シミュレーション期間の総収益計算
 * @param {number} monthlyRevenue - 月間収益
 * @param {number} simulationMonths - シミュレーション期間
 * @returns {number} 総収益
 */
export function calculateTotalRevenue(monthlyRevenue, simulationMonths) {
  return monthlyRevenue * simulationMonths;
}

/**
 * シミュレーション期間の総コスト計算
 * @param {number} monthlyCost - 月間コスト
 * @param {number} simulationMonths - シミュレーション期間
 * @returns {number} 総コスト
 */
export function calculateTotalCost(monthlyCost, simulationMonths) {
  return monthlyCost * simulationMonths;
}

/**
 * プラン評価の総合スコア計算
 * @param {Object} evaluation - 評価結果
 * @param {Object} weights - 重み付け
 * @returns {number} 総合スコア（0-100）
 */
export function calculateOverallScore(evaluation, weights = { profitMargin: 0.5, roi: 0.5 }) {
  const scoreMap = {
    excellent: 100,
    good: 75,
    acceptable: 50,
    poor: 25
  };
  
  const profitScore = scoreMap[evaluation.profitMarginRating] || 0;
  const roiScore = scoreMap[evaluation.roiRating] || 0;
  
  return Math.round(
    profitScore * weights.profitMargin + 
    roiScore * weights.roi
  );
}