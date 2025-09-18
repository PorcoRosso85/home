/**
 * Variables wrapper for JavaScript/MJS files
 * TypeScript変数定義をJavaScriptから利用可能にする
 */

export const REWARD_PLANS = {
  conservative: {
    id: 'conservative',
    name: '手堅く始める',
    tagline: 'リスクを最小限に、成果が出た分だけ支払い',
    structure: '売上の15%を12ヶ月間',
    riskLevel: 'low',
    primaryReason: 'パートナープログラム初心者でもリスクを最小限に抑えて始められる',
    riskFactors: [
      '成果が出なければ費用もゼロ',
      '予算オーバーリスクが極小',
      '短期間での撤退が容易'
    ],
    pros: [
      'リスク最小限',
      '成果連動型で無駄がない',
      '予算管理が容易'
    ],
    cons: [
      '優秀なパートナーには物足りない',
      '成長速度が遅い'
    ],
    bestFor: '初めてのパートナープログラムに最適',
    formula: {
      description: '成果連動型の基本計算式',
      revenueShareRate: 0.15,
      durationMultiplier: 0.5,
      initialBonus: 0,
      calculation: '売上 × 15% × 0.5（12ヶ月限定調整）'
    }
  },
  
  balanced: {
    id: 'balanced',
    name: '有力パートナー向け',
    tagline: '初期インセンティブ＋継続報酬のバランス型',
    structure: '初期3万円＋売上の10%永続',
    riskLevel: 'medium',
    primaryReason: '実績あるパートナーを確実に獲得し、長期関係を構築できる',
    riskFactors: [
      '初期コスト30,000円の先行投資リスク',
      'パートナーの継続的な管理コスト',
      '永続報酬による長期コミット'
    ],
    pros: [
      '実績あるパートナーを引き付ける',
      '長期的な関係構築',
      'バランスの良い報酬体系'
    ],
    cons: [
      '初期コストが発生',
      '管理が複雑'
    ],
    bestFor: '実績のあるパートナーを引き付ける',
    formula: {
      description: '初期ボーナス＋継続報酬の複合式',
      revenueShareRate: 0.10,
      durationMultiplier: 1.0,
      initialBonus: 30000,
      calculation: '初期30,000円 + （売上 × 10% × 1.0）'
    }
  },
  
  aggressive: {
    id: 'aggressive',
    name: '市場支配を狙う',
    tagline: '報酬率を高めに設定し、急速拡大',
    structure: '月間紹介数に応じて15-35%の階層報酬',
    riskLevel: 'high',
    primaryReason: '競合他社からトップパートナーを奪い取り、市場シェアを急速拡大',
    riskFactors: [
      '高い報酬率による利益率圧迫',
      'キャッシュフロー悪化の可能性',
      '一度開始すると報酬引き下げが困難',
      '競合との報酬競争激化リスク'
    ],
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
    bestFor: '競合からパートナーを奪い取る',
    formula: {
      description: '階層型高報酬の変動計算式',
      revenueShareRate: 0.25,
      durationMultiplier: 1.0,
      initialBonus: 0,
      calculation: '売上 × 25%（基準値、実際は15-35%の階層制）'
    }
  }
};

export const DEFAULTS = {
  paybackPeriod: 6,
  riskThreshold: 0.3,
  currencySymbol: '¥',
  locale: 'ja-JP'
};

export const EVALUATION_CRITERIA = {
  profitMargin: {
    excellent: 70,
    good: 50,
    acceptable: 30,
    poor: 0
  },
  roi: {
    excellent: 5.0,
    good: 3.0,
    acceptable: 1.5,
    poor: 1.0
  }
};