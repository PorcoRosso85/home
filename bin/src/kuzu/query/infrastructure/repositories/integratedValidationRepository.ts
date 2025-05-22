/**
 * 統合バリデーション付きリポジトリ
 * Phase 2: バリデーション機能移行版
 */

import { createTemplateValidator } from '../../application/validation/templateValidator';
import { createValidatorDependencies } from '../../domain/validation/validationSchema';
import type { ValidationResult } from '../../domain/types/validationTypes';

// 汎用バリデーションサービス
let validationService: any = null;

async function getValidationService() {
  if (!validationService) {
    const deps = createValidatorDependencies();
    validationService = createTemplateValidator(deps);
  }
  return validationService;
}

/**
 * 新しいバリデーション関数（汎用システム使用）
 */
export async function validateTemplateParameters(queryName: string, params: Record<string, any>): Promise<ValidationResult> {
  const validator = await getValidationService();
  const validateTemplate = validator(queryName);
  return validateTemplate(params);
}

/**
 * パターンマッチによるバリデーション結果処理
 */
export function handleValidationResult(result: ValidationResult): void {
  switch (result.status) {
    case "valid":
      // バリデーション成功 - 何もしない
      break;
    case "validation_error":
      throw new Error(`Validation failed for field '${result.field}': ${result.message}`);
    case "schema_error":
      throw new Error(`Schema error for template '${result.templateName}': ${result.message}`);
    default:
      // 網羅性チェック
      const _exhaustive: never = result;
      throw new Error("未処理のバリデーション結果");
  }
}
