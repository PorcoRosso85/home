/**
 * 汎用クエリ実行サービス
 * 規約準拠: 高階関数依存性注入、パターンマッチ、汎用記述方式
 */

import type { QueryResult, QueryDependencies } from '../../domain/types/queryTypes';

/**
 * 高階関数による汎用クエリサービス作成
 */
export function createQueryService(deps: QueryDependencies) {
  return function executeTemplate(templateName: string) {
    return async function withParams(params: any): Promise<QueryResult> {
      try {
        if (!deps.templateLoader.exists(templateName)) {
          deps.logger.error("Template not found", { templateName });
          return {
            status: "template_not_found",
            templateName,
            message: `Template '${templateName}' not found`
          };
        }

        const template = deps.templateLoader.load(templateName);
        if (!template) {
          return {
            status: "template_not_found",
            templateName,
            message: `Failed to load template '${templateName}'`
          };
        }

        deps.logger.info("Executing template", { templateName });
        const result = await deps.repository.executeQuery(null, templateName, params);
        
        return { status: "success", data: result };

      } catch (error: any) {
        deps.logger.error("Template execution failed", { templateName, error });
        return {
          status: "execution_error",
          code: "EXECUTION_FAILED",
          message: error.message || "Unknown execution error",
          query: templateName
        };
      }
    };
  };
}
