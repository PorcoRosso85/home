/**
 * Service Static Values - 報酬モデル・ジェネレーターの固定値
 * 型安全性を確保したTypeScript版
 */

export interface RewardFormula {
  revenueShareRate: number;
  durationMultiplier: number;
  initialBonus: number;
  description: string;
  calculation: string;
}

export interface RewardPlan {
  id: string;
  name: string;
  tagline: string;
  structure: string;
  riskLevel: 'low' | 'medium' | 'high';
  pros: string[];
  cons: string[];
  riskFactors: string[];
  bestFor: string;
  primaryReason: string;
  formula: RewardFormula;
}

export const REWARD_PLANS: Record<string, RewardPlan> = {
  conservative: {
    id: 'conservative',
    name: '手堅く始める',
    tagline: 'リスクを最小限に、成果が出た分だけ支払い',
    structure: '売上の15%を12ヶ月間',
    riskLevel: 'low',
    pros: [
      'リスク最小限',
      '成果連動型で無駄がない',
      '予算管理が容易'
    ],
    cons: [
      '優秀なパートナーには物足りない',
      '成長速度が遅い'
    ],
    riskFactors: [
      '成果が出なければ費用もゼロ',
      '予算オーバーリスクが極小',
      '短期間での撤退が容易'
    ],
    bestFor: '初めてのパートナープログラムに最適',
    primaryReason: 'パートナープログラム初心者でもリスクを最小限に抑えて始められる',
    formula: {
      revenueShareRate: 0.15,
      durationMultiplier: 0.5,
      initialBonus: 0,
      description: '限定期間の成果報酬型',
      calculation: 'LTV × 15% × 0.5（12ヶ月分）'
    }
  },
  
  balanced: {
    id: 'balanced',
    name: '有力パートナー向け',
    tagline: '初期インセンティブ＋継続報酬のバランス型',
    structure: '初期3万円＋売上の10%永続',
    riskLevel: 'medium',
    pros: [
      '実績あるパートナーを引き付ける',
      '長期的な関係構築',
      'バランスの良い報酬体系'
    ],
    cons: [
      '初期コストが発生',
      '管理が複雑'
    ],
    riskFactors: [
      '初期コスト30,000円の先行投資リスク',
      'パートナーの継続的な管理コスト',
      '永続報酬による長期コミット'
    ],
    bestFor: '実績のあるパートナーを引き付ける',
    primaryReason: '実績あるパートナーを確実に獲得し、長期関係を構築できる',
    formula: {
      revenueShareRate: 0.10,
      durationMultiplier: 1.0,
      initialBonus: 30000,
      description: '初期ボーナス＋永続報酬',
      calculation: '30,000円 + LTV × 10%'
    }
  },
  
  aggressive: {
    id: 'aggressive',
    name: '市場支配を狙う',
    tagline: '報酬率を高めに設定し、急速拡大',
    structure: '月間紹介数に応じて15-35%の階層報酬',
    riskLevel: 'high',
    pros: [
      '競合からパートナーを奪い取る',
      '急速な市場シェア拡大',
      'トップパートナーのモチベーション最大化'
    ],
    cons: [
      '利益率が低下',
      'キャッシュフロー圧迫リスク',
      '撤退が困難'
    ],
    riskFactors: [
      '高い報酬率による利益率圧迫',
      'キャッシュフロー悪化の可能性',
      '一度開始すると報酬引き下げが困難',
      '競合との報酬競争激化リスク'
    ],
    bestFor: '競合からパートナーを奪い取る',
    primaryReason: '競合他社からトップパートナーを奪い取り、市場シェアを急速拡大',
    formula: {
      revenueShareRate: 0.25,
      durationMultiplier: 1.0,
      initialBonus: 0,
      description: '高率の階層報酬型',
      calculation: 'LTV × 25%（平均値）'
    }
  }
};

export interface EnvironmentConfig {
  defaultPaybackPeriod: number;
  defaultRiskThreshold: number;
  currencySymbol: string;
  locale: string;
  evaluation: {
    profitMargin: {
      excellent: number;
      good: number;
      acceptable: number;
    };
    roi: {
      excellent: number;
      good: number;
      acceptable: number;
    };
  };
}

export const ENV_CONFIG: EnvironmentConfig = {
  defaultPaybackPeriod: 6,
  defaultRiskThreshold: 0.3,
  currencySymbol: '¥',
  locale: 'ja-JP',
  evaluation: {
    profitMargin: {
      excellent: 70,
      good: 50,
      acceptable: 30
    },
    roi: {
      excellent: 5.0,
      good: 3.0,
      acceptable: 1.5
    }
  }
};