/**
 * バリデーションエラー処理
 * 規約準拠: throw文禁止、共用体型エラーハンドリング
 */
import type { ValidationError } from '../../../../common/types/errorTypes';

export function createValidationError(
  message: string,
  field?: string,
  code?: string
): ValidationError {
  return {
    status: "validation_error",
    message,
    field,
    code
  };
}

export function isValidationError(result: any): result is ValidationError {
  return result && result.status === "validation_error";
}

export function getValidationErrorDetails(error: ValidationError): {
  message: string;
  field?: string;
  code?: string;
} {
  return {
    message: error.message,
    field: error.field,
    code: error.code
  };
}
