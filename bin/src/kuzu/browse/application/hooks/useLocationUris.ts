import { useState, useEffect } from 'react';
import { fetchLocationUrisCore } from './locationUrisLogic';
import type { LocationUrisState } from '../../domain/types';

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
      
      if (result.success) {
        setState(prev => ({ 
          ...prev, 
          treeData: result.data, 
          loading: false, 
          error: null 
        }));
      } else {
        setState(prev => ({ 
          ...prev, 
          treeData: [],
          loading: false, 
          error: result.error.message 
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
