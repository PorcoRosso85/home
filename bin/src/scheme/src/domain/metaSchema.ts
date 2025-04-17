/**
 * メタスキーマを表すインターフェース
 */
export interface MetaSchema {
  id: string;
  title: string;
  schema: Record<string, any>;
  type: string;
}

/**
 * バリデーション結果を表すインターフェース
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}
