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
