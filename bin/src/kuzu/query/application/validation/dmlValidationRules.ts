/**
 * DML固有バリデーションルール
 * 規約準拠: 汎用記述方式、パターンマッチ
 */

import type { TemplateValidationSchema, ValidationResult } from '../../domain/types/validationTypes';

/**
 * version_batch_operationsのカスタムバリデーター
 */
function validateVersionBatchOperations(params: any): ValidationResult {
  // location_uris配列チェック
  if (!Array.isArray(params.location_uris)) {
    return {
      status: "validation_error",
      field: "location_uris",
      message: "location_uris must be an array",
      value: params.location_uris
    };
  }

  return { status: "valid", data: params };
}

/**
 * DMLテンプレートのバリデーションスキーマ定義
 */
export const dmlValidationSchemas: TemplateValidationSchema[] = [
  {
    templateName: "version_batch_operations",
    rules: [
      { field: "location_uris", required: true, type: "array" },
      { field: "version_id", required: true, type: "string", minLength: 1 }
    ],
    customValidator: validateVersionBatchOperations
  },
  {
    templateName: "create_locationuri",
    rules: [
      { field: "uriId", required: true, type: "string", minLength: 1 },
      { field: "scheme", required: true, type: "string", minLength: 1 },
      { field: "path", required: true, type: "string" }
    ]
  },
  {
    templateName: "create_codeentity", 
    rules: [
      { field: "entityId", required: true, type: "string", minLength: 1 },
      { field: "name", required: true, type: "string", minLength: 1 },
      { field: "entityType", required: true, type: "string", minLength: 1 }
    ]
  }
];
