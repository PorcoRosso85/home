import { useState, useEffect } from 'react';
import { fetchVersionsCore } from './versionStatesLogic';
import type { VersionStatesState } from '../../domain/uiTypes';
import { isErrorResult } from '../../common/typeGuards';

export const useVersionStates = (dbConnection: any | null) => {
  const [state, setState] = useState<VersionStatesState>({
    versions: [],
    loading: false,
    error: null
  });

  useEffect(() => {
    const fetchData = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const result = await fetchVersionsCore({ dbConnection });
      
      if (isErrorResult(result)) {
        setState(prev => ({ 
          ...prev, 
          versions: [],
          loading: false, 
          error: result.message 
        }));
      } else {
        setState(prev => ({ 
          ...prev, 
          versions: result.data, 
          loading: false, 
          error: null 
        }));
      }
    };

    if (dbConnection) {
      fetchData();
    } else {
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
