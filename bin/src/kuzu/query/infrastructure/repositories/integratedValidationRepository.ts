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
 * 規約準拠: throw文禁止、共用体型エラーハンドリング使用
 */
export function handleValidationResult(result: ValidationResult): {success: boolean; error?: string} {
  switch (result.status) {
    case "valid":
      // バリデーション成功
      return {success: true};
    case "validation_error":
      return {success: false, error: `Validation failed for field '${result.field}': ${result.message}`};
    case "schema_error":
      return {success: false, error: `Schema error for template '${result.templateName}': ${result.message}`};
    default:
      // 網羅性チェック
      const _exhaustive: never = result;
      return {success: false, error: "未処理のバリデーション結果"};
  }
}
