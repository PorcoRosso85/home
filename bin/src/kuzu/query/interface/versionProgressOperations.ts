/**
 * バージョン進捗状況管理API
 * 
 * HTTPリクエストを処理してバージョン進捗状況の管理機能を提供する
 */

import type { LocationUriEntity } from '../domain/entities/locationUri';
import type { CompletionStatus } from '../domain/entities/versionState';
import { executeTemplate } from '../application/services/unifiedQueryService';

/**
 * LocationURIの完了状態を設定
 * POST /api/progress/location-uri/mark-completed
 */
export async function markLocationUriCompletedApi(connection: any, body: {
  uriId: string;
  completed: boolean;
}): Promise<{ success: boolean; message: string }> {
  try {
    await executeTemplate(connection, 'mark_locationuri_completed', {
      uri_id: body.uriId,
      completed: body.completed
    });
    return {
      success: true,
      message: `LocationURI ${body.uriId} marked as ${body.completed ? 'completed' : 'incomplete'}`
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 複数LocationURIの完了状態を一括更新
 * POST /api/progress/location-uri/batch-update
 */
export async function batchUpdateLocationUriCompletionApi(connection: any, body: {
  updates: Array<{ uriId: string; completed: boolean }>;
}): Promise<{ 
  success: boolean; 
  message: string;
  updatedCount: number;
}> {
  try {
    await batchUpdateLocationUriCompletion(connection, body.updates);
    return {
      success: true,
      message: `Successfully updated ${body.updates.length} LocationURIs`,
      updatedCount: body.updates.length
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      updatedCount: 0
    };
  }
}

/**
 * 指定バージョンの進捗率を自動計算・更新
 * POST /api/progress/version/calculate
 */
export async function calculateVersionProgressApi(connection: any, body: {
  versionId: string;
}): Promise<{
  success: boolean;
  data?: {
    versionId: string;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  };
  message: string;
}> {
  try {
    const result = await executeTemplate(connection, 'calculate_version_progress', {
      version_id: body.versionId
    });
    return {
      success: true,
      data: result,
      message: 'Version progress calculated successfully'
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * バージョンの進捗率を直接更新
 * POST /api/progress/version/update-progress
 */
export async function updateVersionProgressApi(connection: any, body: {
  versionId: string;
  progressPercentage: number;
}): Promise<{ success: boolean; message: string }> {
  try {
    await executeTemplate(connection, 'update_version_progress', {
      version_id: body.versionId,
      progress_percentage: body.progressPercentage
    });
    return {
      success: true,
      message: `Version ${body.versionId} progress updated to ${(body.progressPercentage * 100).toFixed(1)}%`
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 全バージョンの完了状況サマリーを取得
 * GET /api/progress/version/summary
 */
export async function getCompletionProgressSummaryApi(connection: any): Promise<{
  success: boolean;
  data?: Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completionStatus: CompletionStatus;
  }>;
  message: string;
}> {
  try {
    const data = await getCompletionProgressSummary(connection);
    return {
      success: true,
      data,
      message: 'Completion progress summary retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 指定バージョンの完了状況詳細を取得
 * GET /api/progress/version/status?versionId=...
 */
export async function getVersionCompletionStatusApi(connection: any, query: {
  versionId?: string;
}): Promise<{
  success: boolean;
  data?: Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completedUriList: string[];
    previousVersion: string | null;
    nextVersion: string | null;
  }>;
  message: string;
}> {
  try {
    const data = await getVersionCompletionStatus(connection, query.versionId);
    return {
      success: true,
      data,
      message: 'Version completion status retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 指定バージョンの未完了LocationURI一覧を取得
 * GET /api/progress/version/incomplete-locations?versionId=...
 */
export async function getIncompleteLocationUrisApi(connection: any, query: {
  versionId: string;
}): Promise<{
  success: boolean;
  data?: Array<LocationUriEntity>;
  message: string;
}> {
  try {
    const data = await getIncompleteLocationUris(connection, query.versionId);
    return {
      success: true,
      data,
      message: `Found ${data.length} incomplete LocationURIs for version ${query.versionId}`
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 完了/未完了の統計情報を取得
 * GET /api/progress/statistics
 */
export async function getCompletionStatisticsApi(connection: any): Promise<{
  success: boolean;
  data?: {
    totalVersions: number;
    overallTotalLocations: number;
    overallCompletedLocations: number;
    overallIncompleteLocations: number;
    completionStatusCounts: {
      completed: number;
      in_progress: number;
      not_started: number;
    };
    versionDetails: Array<{
      versionId: string;
      total: number;
      completed: number;
      incomplete: number;
      progress: number;
    }>;
  };
  message: string;
}> {
  try {
    const data = await getCompletionStatistics(connection);
    return {
      success: true,
      data,
      message: 'Completion statistics retrieved successfully'
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * バージョンと関連LocationURIを一括処理
 * POST /api/progress/version/process
 */
export async function processVersionProgressApi(connection: any, body: {
  versionId: string;
  locationUriUpdates: Array<{ uriId: string; completed: boolean }>;
}): Promise<{
  success: boolean;
  data?: {
    versionId: string;
    updatedLocations: number;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  };
  message: string;
}> {
  try {
    const result = await processVersionProgress(
      connection, 
      body.versionId, 
      body.locationUriUpdates
    );
    return {
      success: true,
      data: result,
      message: 'Version progress processed successfully'
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

/**
 * 全バージョンの進捗率を一括再計算
 * POST /api/progress/version/recalculate-all
 */
export async function recalculateAllVersionProgressApi(connection: any): Promise<{
  success: boolean;
  data?: Array<{
    versionId: string;
    previousProgress: number;
    newProgress: number;
    totalLocations: number;
    completedLocations: number;
  }>;
  message: string;
}> {
  try {
    const results = await recalculateAllVersionProgress(connection);
    return {
      success: true,
      data: results,
      message: `Successfully recalculated progress for ${results.length} versions`
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

// HTTP-specific handlers for common frameworks

/**
 * TypeScript Express.js Handler Example
 */
export function createExpressHandlers() {
  return {
    markLocationUriCompleted: async (req: any, res: any) => {
      const result = await markLocationUriCompletedApi(req.connection, req.body);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    batchUpdateLocationUriCompletion: async (req: any, res: any) => {
      const result = await batchUpdateLocationUriCompletionApi(req.connection, req.body);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    calculateVersionProgress: async (req: any, res: any) => {
      const result = await calculateVersionProgressApi(req.connection, req.body);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    updateVersionProgress: async (req: any, res: any) => {
      const result = await updateVersionProgressApi(req.connection, req.body);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    getCompletionProgressSummary: async (req: any, res: any) => {
      const result = await getCompletionProgressSummaryApi(req.connection);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    getVersionCompletionStatus: async (req: any, res: any) => {
      const result = await getVersionCompletionStatusApi(req.connection, req.query);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    getIncompleteLocationUris: async (req: any, res: any) => {
      const result = await getIncompleteLocationUrisApi(req.connection, req.query);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    getCompletionStatistics: async (req: any, res: any) => {
      const result = await getCompletionStatisticsApi(req.connection);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    processVersionProgress: async (req: any, res: any) => {
      const result = await processVersionProgressApi(req.connection, req.body);
      res.status(result.success ? 200 : 400).json(result);
    },
    
    recalculateAllVersionProgress: async (req: any, res: any) => {
      const result = await recalculateAllVersionProgressApi(req.connection);
      res.status(result.success ? 200 : 400).json(result);
    }
  };
}

/**
 * Deno Web Handler Example
 */
export function handleDenoRequest(connection: any) {
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    const path = url.pathname;
    
    try {
      let result;
      
      // GET requests
      if (request.method === 'GET') {
        if (path === '/api/progress/version/summary') {
          result = await getCompletionProgressSummaryApi(connection);
        } else if (path === '/api/progress/version/status') {
          const versionId = url.searchParams.get('versionId') || undefined;
          result = await getVersionCompletionStatusApi(connection, { versionId });
        } else if (path === '/api/progress/version/incomplete-locations') {
          const versionId = url.searchParams.get('versionId');
          if (!versionId) {
            return new Response(JSON.stringify({ 
              success: false, 
              message: 'versionId is required' 
            }), { status: 400 });
          }
          result = await getIncompleteLocationUrisApi(connection, { versionId });
        } else if (path === '/api/progress/statistics') {
          result = await getCompletionStatisticsApi(connection);
        } else {
          return new Response(JSON.stringify({ 
            success: false, 
            message: 'Endpoint not found' 
          }), { status: 404 });
        }
      }
      
      // POST requests
      else if (request.method === 'POST') {
        const body = await request.json();
        
        if (path === '/api/progress/location-uri/mark-completed') {
          result = await markLocationUriCompletedApi(connection, body);
        } else if (path === '/api/progress/location-uri/batch-update') {
          result = await batchUpdateLocationUriCompletionApi(connection, body);
        } else if (path === '/api/progress/version/calculate') {
          result = await calculateVersionProgressApi(connection, body);
        } else if (path === '/api/progress/version/update-progress') {
          result = await updateVersionProgressApi(connection, body);
        } else if (path === '/api/progress/version/process') {
          result = await processVersionProgressApi(connection, body);
        } else if (path === '/api/progress/version/recalculate-all') {
          result = await recalculateAllVersionProgressApi(connection);
        } else {
          return new Response(JSON.stringify({ 
            success: false, 
            message: 'Endpoint not found' 
          }), { status: 404 });
        }
      }
      
      // Method not allowed
      else {
        return new Response(JSON.stringify({ 
          success: false, 
          message: 'Method not allowed' 
        }), { status: 405 });
      }
      
      return new Response(JSON.stringify(result), {
        status: result.success ? 200 : 400,
        headers: { 'Content-Type': 'application/json' }
      });
      
    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        message: error instanceof Error ? error.message : 'Internal server error'
      }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    }
  };
}
