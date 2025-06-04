/**
 * コンテキストメニューのPure Logic（React非依存）
 */
import type { NodeData } from '../../domain/coreTypes';

export type ContextMenuState = {
  show: boolean;
  x: number;
  y: number;
  node: NodeData | null;
};

export type ContextMenuInput = {
  contextMenu: ContextMenuState;
  onContextMenuUpdate: (menu: ContextMenuState) => void;
  onMenuAction: (action: string, node: NodeData) => void;
};

export type ContextMenuOutput = {
  isVisible: boolean;
  position: { x: number; y: number };
  targetNode: NodeData | null;
  handleClose: () => void;
  handleMenuAction: (action: string) => void;
  menuItems: ContextMenuItem[];
};

export type ContextMenuItem = {
  id: string;
  label: string;
  action: string;
  enabled: boolean;
};

export const computeContextMenuCore = (input: ContextMenuInput): ContextMenuOutput => {
  const { contextMenu, onContextMenuUpdate, onMenuAction } = input;

  const handleClose = () => {
    onContextMenuUpdate({ show: false, x: 0, y: 0, node: null });
  };

  const handleMenuAction = (action: string) => {
    if (contextMenu.node) {
      onMenuAction(action, contextMenu.node);
    }
    handleClose();
  };

  // メニュー項目の定義
  const menuItems: ContextMenuItem[] = [
    {
      id: 'claude-analysis',
      label: 'Claude解析',
      action: 'claude-analysis',
      enabled: contextMenu.node?.nodeType === 'version'
    },
    {
      id: 'rust-hello',
      label: 'Rust hello関数作成',
      action: 'rust-hello',
      enabled: true
    },
    {
      id: 'claude-code-echo',
      label: 'Claude-code連携テスト',
      action: 'claude-code-echo',
      enabled: true
    },
    {
      id: 'tmux-claude-echo',
      label: 'tmuxでClaude連携テスト',
      action: 'tmux-claude-echo',
      enabled: contextMenu.node?.nodeType === 'location' || contextMenu.node?.nodeType === 'version'
    },
    {
      id: 'claude-boss-test',
      label: 'Claude親分テスト（2並列）',
      action: 'claude-boss-test',
      enabled: true
    }
  ];

  return {
    isVisible: contextMenu.show,
    position: { x: contextMenu.x, y: contextMenu.y },
    targetNode: contextMenu.node,
    handleClose,
    handleMenuAction,
    menuItems: menuItems.filter(item => item.enabled)
  };
};

export const createContextMenuState = (): ContextMenuState => ({
  show: false,
  x: 0,
  y: 0,
  node: null
});

export const showContextMenu = (
  x: number,
  y: number,
  node: NodeData
): ContextMenuState => ({
  show: true,
  x,
  y,
  node
});
