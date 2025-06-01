import { useState, useEffect } from 'react';
import { fetchLocationUrisCore } from './locationUrisLogic';
import type { LocationUrisState } from '../../domain/types';
import { isErrorResult } from '../../common/typeGuards';

export const useLocationUris = (dbConnection: any | null, selectedVersionId: string) => {
  const [state, setState] = useState<LocationUrisState>({
    treeData: [],
    loading: false,
    error: null
  });

  useEffect(() => {
    const fetchData = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
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
