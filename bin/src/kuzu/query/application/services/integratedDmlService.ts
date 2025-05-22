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
import * as logger from '../../../common/infrastructure/logger';

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
      info: (message: string, meta?: any) => logger.info(message, meta),
      error: (message: string, error?: any) => logger.error(message, error)
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

// createHasLocation を汎用システムで実装
export async function createHasLocation(
  connection: any,
  codeEntityId: string,
  locationUriId: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_has_location');
  
  return executeTemplate({
    codeEntityId,
    locationUriId
  });
}

// createIsImplementedBy を汎用システムで実装
export async function createIsImplementedBy(
  connection: any,
  codeEntityId: string,
  requirementId: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_is_implemented_by');
  
  return executeTemplate({
    codeEntityId,
    requirementId
  });
}

// createReferencesCode を汎用システムで実装
export async function createReferencesCode(
  connection: any,
  sourceEntityId: string,
  targetEntityId: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_references_code');
  
  return executeTemplate({
    sourceEntityId,
    targetEntityId
  });
}

// createVersionState を汎用システムで実装
export async function createVersionState(
  connection: any,
  versionId: string,
  timestamp: string,
  description: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_versionstate');
  
  return executeTemplate({
    versionId,
    timestamp,
    description
  });
}

// trackStateOfCode を汎用システムで実装
export async function trackStateOfCode(
  connection: any,
  versionId: string,
  codeEntityId: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('create_tracks_state_of_located_entity');
  
  return executeTemplate({
    versionId,
    codeEntityId
  });
}

// markLocationUriCompleted を汎用システムで実装
export async function markLocationUriCompleted(
  connection: any,
  uriId: string,
  completionStatus: boolean
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('mark_locationuri_completed');
  
  return executeTemplate({
    uriId,
    completionStatus
  });
}

// calculateVersionProgress を汎用システムで実装
export async function calculateVersionProgress(
  connection: any,
  versionId: string
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('calculate_version_progress');
  
  return executeTemplate({
    versionId
  });
}

// updateVersionProgress を汎用システムで実装
export async function updateVersionProgress(
  connection: any,
  versionId: string,
  completedCount: number,
  totalCount: number
): Promise<QueryResult> {
  const service = await getQueryService();
  const executeTemplate = service('update_version_progress');
  
  return executeTemplate({
    versionId,
    completedCount,
    totalCount
  });
}
