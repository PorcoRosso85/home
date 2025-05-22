/**
 * 統合DMLサービス（汎用システム使用版）
 * Phase 1: 部分移行版
 */

import { createQueryService } from './queryService';
import { createTemplateScanner } from './templateScanner';
import { createQueryRepository } from '../../infrastructure/factories/repositoryFactory';
import type { QueryResult } from '../../domain/types/queryTypes';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

// 依存性を構築
async function createDependencies() {
  const repository = await createQueryRepository();
  const dmlPath = '/home/nixos/bin/src/kuzu/query/dml';
  
  return {
    repository: {
      executeQuery: repository.executeQuery.bind(repository)
    },
    templateLoader: {
      load: (templateName: string) => {
        try {
          const filePath = join(dmlPath, `${templateName}.cypher`);
          return existsSync(filePath) ? readFileSync(filePath, 'utf8') : null;
        } catch { return null; }
      },
      exists: (templateName: string) => existsSync(join(dmlPath, `${templateName}.cypher`)),
      scan: (directory: string) => readdirSync(directory).filter(f => f.endsWith('.cypher'))
    },
    logger: {
      info: (message: string, meta?: any) => console.log(`[INFO] ${message}`, meta || ''),
      error: (message: string, error?: any) => console.error(`[ERROR] ${message}`, error || '')
    }
  };
}

// 汎用サービスのインスタンス
let queryService: any = null;

async function getQueryService() {
  if (!queryService) {
    const deps = await createDependencies();
    queryService = createQueryService(deps);
  }
  return queryService;
}

/**
 * 新しい汎用実行関数（Phase 1移行対象）
 */

// createLocationURI を汎用システムで実装
export async function createLocationURI(
  connection: any,
  uriId: string, 
  scheme: string, 
  path: string,
  locationUris: any[]
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_locationuri');
  
  return executeTemplate({
    uriId,
    scheme, 
    path,
    locationUris
  });
}

// createCodeEntity を汎用システムで実装  
export async function createCodeEntity(
  connection: any,
  entityId: string,
  name: string,
  description: string,
  entityType: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_codeentity');
  
  return executeTemplate({
    entityId,
    name,
    description,
    entityType
  });
}

// createRequirement を汎用システムで実装
export async function createRequirement(
  connection: any,
  requirementId: string,
  description: string,
  priority: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_requirement');
  
  return executeTemplate({
    requirementId,
    description,
    priority
  });
}
