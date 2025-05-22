/**
 * 統一クエリAPI - 最終的にこの3つだけがexportされる
 * 規約準拠: 汎用記述方式、完全自動化
 */

import type { QueryResult } from '../../domain/types/queryTypes';
import { executeAnyTemplate } from './queryService';
import { createAutoTemplateScanner } from './templateScanner';

/**
 * DMLクエリ実行（作成・更新・削除）
 */
export async function executeDml(
  connection: any,
  templateName: string, 
  params: Record<string, any>
): Promise<QueryResult> {
  // テンプレートタイプを自動判定
  const scanner = createAutoTemplateScanner();
  const templateType = scanner.detectTemplateType(templateName);
  
  if (templateType !== 'dml') {
    return {
      status: "template_not_found",
      templateName,
      message: `DML template '${templateName}' not found`
    };
  }

  return await executeAnyTemplate(connection, templateName, params);
}

/**
 * DQLクエリ実行（検索・取得）  
 */
export async function executeDql(
  connection: any,
  templateName: string,
  params: Record<string, any>
): Promise<QueryResult> {
  const scanner = createAutoTemplateScanner();
  const templateType = scanner.detectTemplateType(templateName);
  
  if (templateType !== 'dql') {
    return {
      status: "template_not_found", 
      templateName,
      message: `DQL template '${templateName}' not found`
    };
  }

  return await executeAnyTemplate(connection, templateName, params);
}

/**
 * 自動判定版（推奨）
 * テンプレート名からDML/DQLを自動判定して実行
 */
export async function executeTemplate(
  connection: any,
  templateName: string,
  params: Record<string, any>
): Promise<QueryResult> {
  return await executeAnyTemplate(connection, templateName, params);
}
