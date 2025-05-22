/**
 * バリデーションスキーマ定義
 * 規約準拠: メタデータ駆動型、汎用記述方式
 */

import type { TemplateValidationSchema, ValidatorDependencies } from '../types/validationTypes';
import { dmlValidationSchemas } from '../../application/validation/dmlValidationRules';
import * as logger from '../../../common/infrastructure/logger';

/**
 * スキーマローダーの作成
 */
export function createSchemaLoader(): ValidatorDependencies['schemaLoader'] {
  const schemaMap = new Map<string, TemplateValidationSchema>();
  
  dmlValidationSchemas.forEach(schema => {
    schemaMap.set(schema.templateName, schema);
  });

  return {
    getSchema: (templateName: string) => schemaMap.get(templateName) || null,
    getAllSchemas: () => Array.from(schemaMap.values())
  };
}

/**
 * バリデーション依存性の作成
 */
export function createValidatorDependencies(): ValidatorDependencies {
  return {
    schemaLoader: createSchemaLoader(),
    logger: {
      info: (message: string, meta?: any) => logger.info(message, meta),
      error: (message: string, error?: any) => logger.error(message, error)
    }
  };
}
