/**
 * ユーザー入力パラメータ定義
 * CEOが入力する必須項目とオプション項目
 */

export const USER_PARAMS_SCHEMA = {
  // 必須入力項目
  monthlyPrice: { 
    type: 'number', 
    required: true,
    description: '月額単価',
    example: 20000
  },
  contractMonths: { 
    type: 'number', 
    required: true,
    description: '平均契約期間（月）',
    example: 24
  },
  maxCPA: { 
    type: 'number', 
    required: true,
    description: '許容CPA',
    example: 160000
  },
  
  // オプション項目（デフォルト値あり）
  expectedPartners: { 
    type: 'number', 
    required: false, 
    default: 5,
    description: '月間想定パートナー数'
  },
  simulationMonths: { 
    type: 'number', 
    required: false, 
    default: 6,
    description: 'シミュレーション期間（月）'
  }
};

export function validateUserParams(params) {
  const errors = [];
  
  // 必須項目チェック
  Object.entries(USER_PARAMS_SCHEMA).forEach(([key, schema]) => {
    if (schema.required && (params[key] === undefined || params[key] === null)) {
      errors.push(`${key} is required`);
    }
  });
  
  // 型チェック
  Object.entries(params).forEach(([key, value]) => {
    const schema = USER_PARAMS_SCHEMA[key];
    if (schema && typeof value !== schema.type) {
      errors.push(`${key} must be a ${schema.type}`);
    }
  });
  
  return errors.length > 0 ? { valid: false, errors } : { valid: true };
}

export function applyDefaults(params) {
  const result = { ...params };
  
  Object.entries(USER_PARAMS_SCHEMA).forEach(([key, schema]) => {
    if (!schema.required && result[key] === undefined && schema.default !== undefined) {
      result[key] = schema.default;
    }
  });
  
  return result;
}