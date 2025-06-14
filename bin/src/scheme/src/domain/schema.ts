/**
 * スキーマを表すインターフェース
 */
export interface Schema {
  $schema: string;
  $metaSchema: string;
  type: string;
  title: string;
  description?: string;
  [key: string]: any;
}
