import { useState, useEffect } from 'react';
import { fetchLocationUrisCore } from './locationUrisLogic';
import type { NodeData } from '../../domain/coreTypes';
import { isErrorResult } from '../../common/typeGuards';

/**
 * LocationURI状態型（CONVENTION.yaml準拠）
 */
type LocationUrisState = {
  treeData: NodeData[];
  loading: boolean;
  error: string | null;
};

/**
 * LocationURI状態管理のReact Hook（薄いWrapper）
 * CONVENTION.yaml準拠: Core関数を使用し、React状態管理のみに責務を限定
 */
export const useLocationUris = (dbConnection: any | null, selectedVersionId: string) => {
  const [state, setState] = useState<LocationUrisState>({
    treeData: [],
    loading: false,
    error: null
  });

  useEffect(() => {
    const fetchData = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Core関数呼び出し（規約準拠）
      const result = await fetchLocationUrisCore({ dbConnection, selectedVersionId });
      
      if (isErrorResult(result)) {
        setState(prev => ({ 
          ...prev, 
          treeData: [],
          loading: false, 
          error: result.message 
        }));
      } else {
        setState(prev => ({ 
          ...prev, 
          treeData: result.data, 
          loading: false, 
          error: null 
        }));
      }
    };

    if (dbConnection && selectedVersionId) {
      fetchData();
    } else {
      setState(prev => ({ 
        ...prev, 
        treeData: [], 
        loading: false, 
        error: null 
      }));
    }
  }, [dbConnection, selectedVersionId]);

  return state;
};
