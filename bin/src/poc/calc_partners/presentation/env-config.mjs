/**
 * 環境設定値
 * 業界標準値やシステム設定
 */

export const ENV_CONFIG = {
  // 業界標準値
  defaultPaybackPeriod: Number(process.env.PAYBACK_PERIOD) || 6,  // 標準投資回収期間（月）
  defaultRiskThreshold: Number(process.env.RISK_THRESHOLD) || 0.3, // リスク閾値（30%）
  
  // 表示設定
  currencySymbol: process.env.CURRENCY || '¥',
  locale: process.env.LOCALE || 'ja-JP',
  
  // 計算設定
  maxSimulationMonths: Number(process.env.MAX_SIMULATION_MONTHS) || 12,
  minProfitMargin: Number(process.env.MIN_PROFIT_MARGIN) || 0.2, // 最低利益率20%
  
  // プラン評価基準（環境依存）
  evaluation: {
    profitMargin: {
      excellent: Number(process.env.PROFIT_EXCELLENT) || 70,
      good: Number(process.env.PROFIT_GOOD) || 50,
      acceptable: Number(process.env.PROFIT_ACCEPTABLE) || 30
    },
    roi: {
      excellent: Number(process.env.ROI_EXCELLENT) || 5.0,
      good: Number(process.env.ROI_GOOD) || 3.0,
      acceptable: Number(process.env.ROI_ACCEPTABLE) || 1.5
    }
  }
};

/**
 * 環境設定の検証
 */
export function validateEnvConfig() {
  const warnings = [];
  
  if (ENV_CONFIG.defaultPaybackPeriod < 3 || ENV_CONFIG.defaultPaybackPeriod > 24) {
    warnings.push('Payback period outside typical range (3-24 months)');
  }
  
  if (ENV_CONFIG.defaultRiskThreshold < 0.1 || ENV_CONFIG.defaultRiskThreshold > 0.5) {
    warnings.push('Risk threshold outside typical range (10-50%)');
  }
  
  return warnings;
}