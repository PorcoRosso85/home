/**
 * コンテキストメニューUI（薄いReactラッパー）
 */
import React from 'react';
import { computeContextMenuCore, type ContextMenuInput } from './contextMenu';

interface ContextMenuProps extends ContextMenuInput {}

export const ContextMenu: React.FC<ContextMenuProps> = (props) => {
  const menuLogic = computeContextMenuCore(props);

  if (!menuLogic.isVisible) {
    return null;
  }

  return (
    <>
      {/* バックドロップ */}
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 999
        }}
        onClick={menuLogic.handleClose}
      />
      
      {/* メニュー本体 */}
      <div
        style={{
          position: 'fixed',
          top: menuLogic.position.y,
          left: menuLogic.position.x,
          backgroundColor: 'white',
          border: '1px solid #ccc',
          borderRadius: '4px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          zIndex: 1000,
          minWidth: '150px'
        }}
      >
        {menuLogic.menuItems.map((item) => (
          <button
            key={item.id}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: 'none',
              backgroundColor: 'transparent',
              textAlign: 'left',
              cursor: 'pointer'
            }}
            onClick={() => menuLogic.handleMenuAction(item.action)}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f0f0'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            {item.label}
          </button>
        ))}
      </div>
    </>
  );
};
