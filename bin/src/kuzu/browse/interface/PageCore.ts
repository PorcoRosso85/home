import type { PageInput, PageOutput } from '../../domain/types';

/**
 * ページロジックのCore関数（Pure Logic）
 */
export const createPageLogicCore = () => {
  let selectedVersionId = '';

  const handleVersionClick = (versionId: string) => {
    selectedVersionId = versionId;
    console.log(`Version ${versionId} selected`);
  };

  const computePageState = (input: PageInput): PageOutput => {
    const shouldShowConnectionError = !!input.connectionError;
    const shouldShowConnectionWaiting = !input.isConnected && !input.connectionError;
    const shouldShowMainContent = input.isConnected && !input.connectionError;

    return {
      selectedVersionId,
      handleVersionClick,
      shouldShowConnectionError,
      shouldShowConnectionWaiting,
      shouldShowMainContent,
      connectionErrorMessage: input.connectionError || undefined
    };
  };

  const updateSelectedVersion = (versionId: string) => {
    selectedVersionId = versionId;
  };

  const getSelectedVersion = () => selectedVersionId;

  return {
    computePageState,
    handleVersionClick,
    updateSelectedVersion,
    getSelectedVersion
  };
};

export type PageLogicCore = ReturnType<typeof createPageLogicCore>;
