/**
 * テンプレートバリデーター
 * 規約準拠: 高階関数依存性注入、パターンマッチ、汎用記述方式
 */

import type { ValidationResult, ValidatorDependencies, ValidationRule } from '../../domain/types/validationTypes';
import { validateField } from './fieldValidator';

/**
 * 高階関数によるテンプレートバリデーター作成
 */
export function createTemplateValidator(deps: ValidatorDependencies) {
  return function validateTemplate(templateName: string) {
    return function withParams(params: any): ValidationResult {
      try {
        // スキーマ取得
        const schema = deps.schemaLoader.getSchema(templateName);
        if (!schema) {
          deps.logger.info("No validation schema found", { templateName });
          return { status: "valid", data: params };
        }

        // カスタムバリデーター実行
        if (schema.customValidator) {
          const customResult = schema.customValidator(params);
          if (customResult.status !== "valid") {
            return customResult;
          }
        }

        // ルールベースバリデーション
        for (const rule of schema.rules) {
          const fieldResult = validateField(params, rule);
          if (fieldResult.status !== "valid") {
            deps.logger.error("Validation failed", { templateName, field: rule.field });
            return fieldResult;
          }
        }

        deps.logger.info("Validation successful", { templateName });
        return { status: "valid", data: params };

      } catch (error: any) {
        deps.logger.error("Validation error", { templateName, error });
        return {
          status: "schema_error", 
          message: error.message || "Unknown validation error",
          templateName
        };
      }
    };
  };
}
