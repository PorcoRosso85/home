import type { 
  VersionStatesInput, 
  VersionStatesOutput, 
  NodeData, 
  NodeClickEvent 
} from '../../domain/types';
import { showContextMenu } from '../components/contextMenu';

export const computeVersionStatesCore = (
  input: VersionStatesInput,
  onExpandedVersionsUpdate: (newExpanded: Set<string>) => void,
  onContextMenuUpdate: (menu: VersionStatesInput['contextMenu']) => void,
  onClaudeRequest: (prompt: string, node: NodeData) => void
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
      const newContextMenu = showContextMenu(
        clickEvent.event.clientX,
        clickEvent.event.clientY,
        clickEvent.node
      );
      onContextMenuUpdate(newContextMenu);
      clickEvent.event.preventDefault();
    }
  };

  // プロンプト生成ロジック
  const generatePrompt = (action: string, node: NodeData): string => {
    switch (action) {
      case 'claude-analysis':
        return `バージョン${node.id}の解析を行ってください。詳細: ${node.name}`;
      case 'rust-hello':
        return '/home/nixos/bin/src/tmp/hello.rs\nここにhelloを返す関数とそれをコンソール出力するためのテストをインソーステストとして記述して';
      default:
        return `不明なアクション: ${action}`;
    }
  };

  // コンテキストメニューのロジックは分離されたコンポーネントに委譲
  const handleMenuAction = (action: string, node: NodeData) => {
    const prompt = generatePrompt(action, node);
    onClaudeRequest(prompt, node);
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
    handleMenuAction
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
