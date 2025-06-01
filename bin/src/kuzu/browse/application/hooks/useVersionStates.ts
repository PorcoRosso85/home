import { useState, useEffect } from 'react';
import { fetchVersionsCore } from './versionStatesLogic';
import type { VersionStatesState } from '../../domain/types';

/**
 * バージョン状態管理のReact Hook（薄いWrapper）
 * Core関数を使用し、React状態管理のみに責務を限定
 */
export const useVersionStates = (dbConnection: any | null) => {
  const [state, setState] = useState<VersionStatesState>({
    versions: [],
    loading: false,
    error: null
  });

  useEffect(() => {
    const fetchData = async () => {
      // Hook層：React状態の更新
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Core関数呼び出し
      const result = await fetchVersionsCore({ dbConnection });
      
      if (result.success) {
        // Hook層：成功時のReact状態更新
        setState(prev => ({ 
          ...prev, 
          versions: result.data, 
          loading: false, 
          error: null 
        }));
      } else {
        // Hook層：エラー時のReact状態更新（UI表示用メッセージのみ）
        setState(prev => ({ 
          ...prev, 
          versions: [],
          loading: false, 
          error: result.error.message 
        }));
      }
    };

    if (dbConnection) {
      fetchData();
    } else {
      // Hook層：接続なし時の状態リセット
      setState(prev => ({ 
        ...prev, 
        versions: [], 
        loading: false, 
        error: null 
      }));
    }
  }, [dbConnection]);

  return state;
};
