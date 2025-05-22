/**
 * バリデーション関連の型定義
 * 規約準拠: type定義優先、Tagged Union、汎用記述方式
 */

// バリデーション成功・エラー型（Tagged Union）
type ValidationSuccess = {
  status: "valid";
  data: any;
};

type ValidationFieldError = {
  status: "validation_error";
  field: string;
  message: string;
  value?: any;
};

type ValidationSchemaError = {
  status: "schema_error";
  message: string;
  templateName: string;
};

// 共用体型
export type ValidationResult = ValidationSuccess | ValidationFieldError | ValidationSchemaError;

// バリデーションルール定義
export type ValidationRule = {
  field: string;
  required: boolean;
  type: "string" | "number" | "boolean" | "array" | "object";
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  allowedValues?: any[];
  validator?: (value: any) => boolean;
};

export type TemplateValidationSchema = {
  templateName: string;
  rules: ValidationRule[];
  customValidator?: (params: any) => ValidationResult;
};

// 依存性注入用型定義
export type ValidatorDependencies = {
  schemaLoader: {
    getSchema: (templateName: string) => TemplateValidationSchema | null;
    getAllSchemas: () => TemplateValidationSchema[];
  };
  logger: {
    info: (message: string, meta?: any) => void;
    error: (message: string, error?: any) => void;
  };
};
