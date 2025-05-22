/**
 * 汎用クエリ実行サービス（完全自動化版）
 * 規約準拠: 高階関数依存性注入、パターンマッチ、汎用記述方式
 */

import type { QueryResult, QueryDependencies } from '../../domain/types/queryTypes';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

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

/**
 * 完全自動化された汎用クエリ実行関数
 * DML/DQLディレクトリを自動検索し、適切なリポジトリ関数を呼び出す
 */
export async function executeAnyTemplate(
  connection: any,
  templateName: string, 
  params: Record<string, any> = {}
): Promise<QueryResult> {
  try {
    // 1. DMLディレクトリで検索
    const dmlPath = join(process.cwd(), 'dml', `${templateName}.cypher`);
    if (existsSync(dmlPath)) {
      const template = readFileSync(dmlPath, 'utf-8');
      const extractedParams = extractTemplateParams(template);
      
      // パラメータ検証
      const validation = validateParams(params, extractedParams);
      if (!validation.isValid) {
        return {
          status: "validation_error",
          code: "INVALID_PARAMS",
          message: `Invalid parameters: ${validation.errors.join(', ')}`,
          templateName
        };
      }

      // DMLリポジトリで実行
      const { createQueryRepository } = await import('../../infrastructure/factories/repositoryFactory');
      const repository = await createQueryRepository();
      const result = await repository.executeDmlQuery(connection, templateName, params);
      
      return { status: "success", data: result, templateType: "dml" };
    }

    // 2. DQLディレクトリで検索  
    const dqlPath = join(process.cwd(), 'dql', `${templateName}.cypher`);
    if (existsSync(dqlPath)) {
      const template = readFileSync(dqlPath, 'utf-8');
      const extractedParams = extractTemplateParams(template);
      
      // パラメータ検証
      const validation = validateParams(params, extractedParams);
      if (!validation.isValid) {
        return {
          status: "validation_error", 
          code: "INVALID_PARAMS",
          message: `Invalid parameters: ${validation.errors.join(', ')}`,
          templateName
        };
      }

      // DQLリポジトリで実行
      const { createQueryRepository } = await import('../../infrastructure/factories/repositoryFactory');
      const repository = await createQueryRepository();
      const result = await repository.executeDqlQuery(connection, templateName, params);
      
      return { status: "success", data: result, templateType: "dql" };
    }

    // 3. テンプレートが見つからない場合
    return {
      status: "template_not_found",
      templateName,
      message: `Template '${templateName}' not found in dml/ or dql/ directories`
    };

    } catch (error: any) {
      return {
        status: "execution_error",
        code: "EXECUTION_FAILED", 
        message: error?.message || "Unknown execution error",
        query: templateName
      };
    }
}

/**
 * テンプレートからパラメータを自動抽出
 */
function extractTemplateParams(templateContent: string): string[] {
  const paramRegex = /\$(\w+)/g;
  const params: string[] = [];
  let match;
  
  while ((match = paramRegex.exec(templateContent)) !== null) {
    if (!params.includes(match[1])) {
      params.push(match[1]);
    }
  }
  
  return params;
}

/**
 * パラメータ検証
 */
function validateParams(
  provided: Record<string, any>,
  required: string[]
): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  for (const param of required) {
    if (!(param in provided)) {
      errors.push(`Missing required parameter: ${param}`);
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}