/**
 * 階層型トレーサビリティモデル - 結果型定義
 * 規約準拠: type定義優先、最小構成
 */

export type RequirementResult = {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  requirement_priority: string;
  implementation_type: string;
  requirement_location: string;
  relation_type: string;
};

export type ImplementationResult = {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  code_id: string;
  code_name: string;
  code_type: string;
  implementation_type: string;
  code_location: string;
};

export type UnimplementedResult = {
  requirement_id: string;
  title: string;
};
