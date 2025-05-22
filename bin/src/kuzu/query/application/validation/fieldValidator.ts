/**
 * フィールドバリデーション関数
 * 規約準拠: 汎用記述方式、パターンマッチ
 */

import type { ValidationResult, ValidationRule } from '../../domain/types/validationTypes';

/**
 * フィールドバリデーション関数
 */
export function validateField(params: any, rule: ValidationRule): ValidationResult {
  const value = params[rule.field];
  
  // 必須チェック
  if (rule.required && (value === undefined || value === null)) {
    return {
      status: "validation_error",
      field: rule.field,
      message: `Field '${rule.field}' is required`,
      value
    };
  }

  // 値が存在しない場合は必須でなければ通す
  if (value === undefined || value === null) {
    return { status: "valid", data: value };
  }

  // 型チェック（パターンマッチ）
  switch (rule.type) {
    case "string":
      if (typeof value !== "string") {
        return {
          status: "validation_error",
          field: rule.field,
          message: `Field '${rule.field}' must be a string`,
          value
        };
      }
      break;
    case "number":
      if (typeof value !== "number") {
        return {
          status: "validation_error",
          field: rule.field,
          message: `Field '${rule.field}' must be a number`,
          value
        };
      }
      break;
    case "boolean":
      if (typeof value !== "boolean") {
        return {
          status: "validation_error",
          field: rule.field,
          message: `Field '${rule.field}' must be a boolean`,
          value
        };
      }
      break;
  }

  return { status: "valid", data: value };
}
