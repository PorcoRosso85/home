import type { 
  VersionStatesInput, 
  VersionStatesOutput, 
  NodeData, 
  NodeClickEvent 
} from '../../domain/types';

export const computeVersionStatesCore = (
  input: VersionStatesInput,
  onExpandedVersionsUpdate: (newExpanded: Set<string>) => void,
  onContextMenuUpdate: (menu: VersionStatesInput['contextMenu']) => void,
  onClaudeAnalysis: (node: NodeData) => void
): VersionStatesOutput => {
  
  const shouldShowLoading = input.loading;
  const shouldShowError = !!input.error;
  const shouldShowEmpty = !input.loading && !input.error && input.versions.length === 0;
  const shouldShowLocationError = !!input.locationError;
  const shouldShowMainContent = !input.loading && !input.error && input.versions.length > 0;

  const versionTree = buildVersionTreeCore(input);

  const handleVersionNodeClick = (clickEvent: NodeClickEvent) => {
    if (clickEvent.eventType === 'left' && clickEvent.node.nodeType === 'version') {
      input.onVersionClick(clickEvent.node.id);
      
      const newExpanded = new Set(input.expandedVersions);
      if (newExpanded.has(clickEvent.node.id)) {
        newExpanded.delete(clickEvent.node.id);
      } else {
        newExpanded.add(clickEvent.node.id);
      }
      onExpandedVersionsUpdate(newExpanded);
    }
    else if (clickEvent.eventType === 'right' && clickEvent.node.nodeType === 'version') {
      onContextMenuUpdate({
        show: true,
        x: clickEvent.event.clientX,
        y: clickEvent.event.clientY,
        node: clickEvent.node
      });
      clickEvent.event.preventDefault();
    }
  };

  const handleClaudeAnalysis = () => {
    if (input.contextMenu.node) {
      onClaudeAnalysis(input.contextMenu.node);
      onContextMenuUpdate({ show: false, x: 0, y: 0, node: null });
    }
  };

  const handleCloseContextMenu = () => {
    onContextMenuUpdate({ show: false, x: 0, y: 0, node: null });
  };

  return {
    shouldShowLoading,
    shouldShowError,
    shouldShowEmpty,
    shouldShowLocationError,
    shouldShowMainContent,
    errorMessage: input.error || undefined,
    locationErrorMessage: input.locationError || undefined,
    emptyMessage: "利用可能なバージョンがありません。",
    versionTree,
    handleVersionNodeClick,
    handleClaudeAnalysis,
    handleCloseContextMenu
  };
};

export const buildVersionTreeCore = (input: VersionStatesInput): NodeData[] => {
  return input.versions.map(version => {
    const isExpanded = input.expandedVersions.has(version.id);
    const baseNode: NodeData = {
      id: version.id,
      name: `${version.id} - ${version.description}`,
      nodeType: 'version',
      children: [],
      from_version: version.id,
      isCurrentVersion: version.id === input.selectedVersionId
    };

    if (isExpanded && version.id === input.selectedVersionId && input.locationTreeData.length > 0) {
      baseNode.children = input.locationTreeData;
    }

    return baseNode;
  });
};
