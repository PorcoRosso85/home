/**
 * Generate Queries Command
 * 
 * クエリ生成に関するコマンド関数群
 */

import type { QueryResult } from '../../domain/entities/queryResult';
import { 
  processEntity, 
  processAllEntities, 
  type EntityDefinition 
} from '../../infrastructure/tools/dmlGenerator';

/**
 * 単一エンティティからクエリを生成する
 */
export async function generateQueriesForEntity(
  entityPath: string,
  outputDir?: string
): Promise<QueryResult<void>> {
  try {
    await processEntity(entityPath, outputDir);
    return {
      success: true,
      data: undefined
    };
  } catch (error) {
    return {
      success: false,
      error: `エンティティクエリ生成中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * 全エンティティからクエリを生成する
 */
export async function generateAllQueries(
  inputDir?: string,
  outputDir?: string
): Promise<QueryResult<number>> {
  try {
    const entityCount = await processAllEntities(inputDir, outputDir);
    return {
      success: true,
      data: entityCount
    };
  } catch (error) {
    return {
      success: false,
      error: `クエリ一括生成中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * エンティティ定義から動的にクエリを生成する
 */
export async function generateQueryFromDefinition(
  entityDefinition: EntityDefinition,
  templateType: string
): Promise<QueryResult<string>> {
  try {
    const { generateQuery } = await import('../../infrastructure/tools/dmlGenerator');
    const query = generateQuery(entityDefinition, templateType);
    
    return {
      success: true,
      data: query
    };
  } catch (error) {
    return {
      success: false,
      error: `クエリ動的生成中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * クエリテンプレートを生成する（カスタマイズ用）
 */
export async function generateQueryTemplate(
  entityType: 'node' | 'edge',
  templateType: 'create' | 'match' | 'update' | 'delete',
  tableName: string,
  properties: Record<string, { type: string; primary_key?: boolean }>,
  fromTable?: string,
  toTable?: string
): Promise<QueryResult<string>> {
  try {
    const { generateQuery } = await import('../../infrastructure/tools/dmlGenerator');
    
    const entityDefinition: EntityDefinition = {
      entity_type: entityType,
      table_name: tableName,
      templates: [templateType],
      properties,
      from_table: fromTable,
      to_table: toTable
    };
    
    const query = generateQuery(entityDefinition, templateType);
    
    return {
      success: true,
      data: query
    };
  } catch (error) {
    return {
      success: false,
      error: `クエリテンプレート生成中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * 進捗報告付きでクエリを一括生成する
 */
export async function generateQueriesWithProgress(
  inputDir?: string,
  outputDir?: string,
  onProgress?: (message: string, total?: number, current?: number) => void
): Promise<QueryResult<number>> {
  try {
    onProgress?.('クエリ生成を開始します...');
    
    // エンティティファイルのリストを取得
    const fs = await import('fs');
    const path = await import('path');
    
    const targetDir = inputDir || path.join(process.cwd(), 'dml');
    const entityFiles = fs.readdirSync(targetDir)
      .filter(file => file.endsWith('.json'));
    
    const total = entityFiles.length;
    onProgress?.(`${total}個のエンティティファイルを処理します`, total, 0);
    
    // 各エンティティを処理
    let processedCount = 0;
    for (const entityFile of entityFiles) {
      const entityPath = path.join(targetDir, entityFile);
      onProgress?.(`処理中: ${entityFile}`, total, processedCount + 1);
      
      await processEntity(entityPath, outputDir);
      processedCount++;
    }
    
    onProgress?.('クエリ生成が完了しました', total, total);
    
    return {
      success: true,
      data: processedCount
    };
  } catch (error) {
    return {
      success: false,
      error: `進捗報告付きクエリ生成中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * クエリ生成の設定を検証する
 */
export async function validateQueryGenerationConfig(
  inputDir: string,
  outputDir: string
): Promise<QueryResult<{ valid: boolean; issues: string[] }>> {
  try {
    const fs = await import('fs');
    const issues: string[] = [];
    
    // 入力ディレクトリのチェック
    if (!fs.existsSync(inputDir)) {
      issues.push(`入力ディレクトリが存在しません: ${inputDir}`);
    } else {
      const jsonFiles = fs.readdirSync(inputDir).filter(file => file.endsWith('.json'));
      if (jsonFiles.length === 0) {
        issues.push(`入力ディレクトリにエンティティファイル(.json)が見つかりません: ${inputDir}`);
      }
    }
    
    // 出力ディレクトリのチェック
    if (!fs.existsSync(outputDir)) {
      try {
        fs.mkdirSync(outputDir, { recursive: true });
      } catch (error) {
        issues.push(`出力ディレクトリを作成できません: ${outputDir}`);
      }
    } else {
      // 書き込み権限のチェック
      try {
        const testFile = `${outputDir}/.write-test`;
        fs.writeFileSync(testFile, 'test');
        fs.unlinkSync(testFile);
      } catch (error) {
        issues.push(`出力ディレクトリへの書き込み権限がありません: ${outputDir}`);
      }
    }
    
    return {
      success: true,
      data: {
        valid: issues.length === 0,
        issues
      }
    };
  } catch (error) {
    return {
      success: false,
      error: `設定検証中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}
