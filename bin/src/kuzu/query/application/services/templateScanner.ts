/**
 * テンプレートスキャナー
 * 規約準拠: 高階関数依存性注入、汎用記述方式
 */

import type { TemplateScannerDependencies } from '../../domain/types/queryTypes';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

/**
 * 高階関数によるテンプレートスキャナー作成
 */
export function createTemplateScanner(deps: TemplateScannerDependencies) {
  return {
    scan: function scanDirectory(directory: string): string[] {
      try {
        if (!deps.fileSystem.exists(directory)) {
          deps.logger.error("Directory not found", { directory });
          return [];
        }

        const files = deps.fileSystem.readDir(directory);
        const cypherFiles = files.filter(file => file.endsWith('.cypher'));
        
        deps.logger.info("Scanned templates", { directory, count: cypherFiles.length });
        return cypherFiles.map(file => file.replace('.cypher', ''));
      } catch (error: any) {
        deps.logger.error("Template scan failed", { directory, error });
        return [];
      }
    },

    load: function loadTemplate(templateName: string, directory: string): string | null {
      try {
        const filePath = join(directory, `${templateName}.cypher`);
        if (!deps.fileSystem.exists(filePath)) return null;

        const content = deps.fileSystem.readFile(filePath);
        deps.logger.info("Template loaded", { templateName });
        return content;
      } catch (error: any) {
        deps.logger.error("Template load failed", { templateName, error });
        return null;
      }
    },

    exists: function templateExists(templateName: string, directory: string): boolean {
      const filePath = join(directory, `${templateName}.cypher`);
      return deps.fileSystem.exists(filePath);
    }
  };
}

/**
 * 完全自動化されたテンプレートスキャナー
 * DML/DQL両方を自動スキャンし、テンプレートレジストリを作成
 */
export function createAutoTemplateScanner() {
  return {
    /**
     * DML/DQL両方を自動スキャン
     */
    scanAllTemplates: async (): Promise<TemplateRegistry> => {
      const dmlDir = join(process.cwd(), 'dml');
      const dqlDir = join(process.cwd(), 'dql');
      
      const registry: TemplateRegistry = {
        dml: {},
        dql: {},
        all: []
      };

      // DMLテンプレートスキャン
      if (existsSync(dmlDir)) {
        const dmlFiles = readdirSync(dmlDir).filter(file => file.endsWith('.cypher'));
        for (const file of dmlFiles) {
          const templateName = file.replace('.cypher', '');
          const content = readFileSync(join(dmlDir, file), 'utf-8');
          const params = extractTemplateParams(content);
          
          registry.dml[templateName] = {
            name: templateName,
            type: 'dml',
            path: join(dmlDir, file),
            params,
            content
          };
          registry.all.push(templateName);
        }
      }

      // DQLテンプレートスキャン
      if (existsSync(dqlDir)) {
        const dqlFiles = readdirSync(dqlDir).filter(file => file.endsWith('.cypher'));
        for (const file of dqlFiles) {
          const templateName = file.replace('.cypher', '');
          const content = readFileSync(join(dqlDir, file), 'utf-8');
          const params = extractTemplateParams(content);
          
          registry.dql[templateName] = {
            name: templateName,
            type: 'dql',
            path: join(dqlDir, file),
            params,
            content
          };
          registry.all.push(templateName);
        }
      }

      return registry;
    },

    /**
     * テンプレート名から自動的にタイプ判定
     */
    detectTemplateType: (name: string): 'dml' | 'dql' | null => {
      const dmlPath = join(process.cwd(), 'dml', `${name}.cypher`);
      const dqlPath = join(process.cwd(), 'dql', `${name}.cypher`);
      
      if (existsSync(dmlPath)) return 'dml';
      if (existsSync(dqlPath)) return 'dql';
      return null;
    },

    /**
     * パラメータ自動抽出
     */
    extractParams: (templateContent: string): string[] => {
      return extractTemplateParams(templateContent);
    }
  };
}

/**
 * テンプレートレジストリの型定義
 */
export interface TemplateRegistry {
  dml: Record<string, TemplateInfo>;
  dql: Record<string, TemplateInfo>;
  all: string[];
}

export interface TemplateInfo {
  name: string;
  type: 'dml' | 'dql';
  path: string;
  params: string[];
  content: string;
}

/**
 * テンプレートからパラメータを自動抽出（ヘルパー関数）
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
