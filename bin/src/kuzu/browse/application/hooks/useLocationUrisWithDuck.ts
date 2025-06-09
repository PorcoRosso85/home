/**
 * LocationURIデータ取得フックの改良版
 * Duck APIからParquetをダウンロードしてKuzuにロードする
 */
import { useState, useEffect } from 'react';
import { fetchLocationUrisCore } from './locationUrisLogic';
import { loadLocationUrisFromDuck } from '../usecase/loadLocationUrisFromDuck';
import type { NodeData } from '../../domain/coreTypes';
import { isErrorResult } from '../../common/typeGuards';
import * as logger from '../../../common/infrastructure/logger';

/**
 * LocationURI状態型（CONVENTION.yaml準拠）
 */
type LocationUrisState = {
  treeData: NodeData[];
  loading: boolean;
  error: string | null;
  loadedVersion: string | null; // 現在ロード済みのバージョン
};

/**
 * LocationURI状態管理のReact Hook（Duck API統合版）
 */
export const useLocationUris = (dbConnection: any | null, selectedVersionId: string) => {
  const [state, setState] = useState<LocationUrisState>({
    treeData: [],
    loading: false,
    error: null,
    loadedVersion: null
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!dbConnection || !selectedVersionId) {
        setState(prev => ({ 
          ...prev, 
          treeData: [], 
          loading: false, 
          error: null 
        }));
        return;
      }

      // すでに同じバージョンがロード済みの場合はスキップ
      if (state.loadedVersion === selectedVersionId) {
        logger.debug(`[useLocationUris] Version ${selectedVersionId} already loaded`);
        return;
      }

      setState(prev => ({ ...prev, loading: true, error: null }));
      
      try {
        // 1. まずKuzuに該当バージョンのLocationURIが存在するか確認
        const checkQuery = `
          MATCH (v:VersionState {id: '${selectedVersionId}'})
          OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
          RETURN count(l) as count
        `;
        
        const checkResult = await dbConnection.query(checkQuery);
        const checkData = await checkResult.getAllObjects();
        await checkResult.close();
        
        const existingCount = checkData[0]?.count || 0;
        logger.info(`[useLocationUris] Found ${existingCount} existing LocationURI nodes for version ${selectedVersionId}`);
        
        // 2. LocationURIが存在しない場合はDuck APIからロード
        if (existingCount === 0) {
          logger.info(`[useLocationUris] Loading LocationURI data from Duck API for version ${selectedVersionId}`);
          
          // バージョン番号を抽出（ducklake-v1 → 1）
          const versionMatch = selectedVersionId.match(/ducklake-v(\d+)/);
          if (!versionMatch) {
            setState(prev => ({ 
              ...prev, 
              loading: false, 
              error: `Invalid version ID format: ${selectedVersionId}` 
            }));
            return;
          }
          
          const versionNum = parseInt(versionMatch[1]);
          const loadResult = await loadLocationUrisFromDuck(dbConnection, versionNum);
          
          if ('code' in loadResult) {
            setState(prev => ({ 
              ...prev, 
              loading: false, 
              error: loadResult.message 
            }));
            return;
          }
          
          logger.info(`[useLocationUris] Successfully loaded ${loadResult.loadedCount} LocationURI nodes`);
        }
        
        // 3. Core関数呼び出し（既存のロジックを使用）
        const result = await fetchLocationUrisCore({ dbConnection, selectedVersionId });
        
        if (isErrorResult(result)) {
          setState(prev => ({ 
            ...prev, 
            treeData: [],
            loading: false, 
            error: result.message,
            loadedVersion: null
          }));
        } else {
          setState(prev => ({ 
            ...prev, 
            treeData: result.data, 
            loading: false, 
            error: null,
            loadedVersion: selectedVersionId
          }));
        }
      } catch (error) {
        logger.error('[useLocationUris] Unexpected error:', error);
        setState(prev => ({ 
          ...prev, 
          loading: false, 
          error: `Unexpected error: ${error instanceof Error ? error.message : String(error)}`,
          loadedVersion: null
        }));
      }
    };

    fetchData();
  }, [dbConnection, selectedVersionId]); // state.loadedVersionは依存配列に含めない（無限ループ防止）

  return state;
};
