/**
 * 右クリック時の小さなDQLメニューポップアップ
 */
import React from 'react';
import { copyDQLToClipboard } from '../../application/utils/dqlClipboard';

interface ContextMenuProps {
  x: number;
  y: number;
  selectedVersionId?: string;
  onClose: () => void;
}

export const ContextMenu: React.FC<ContextMenuProps> = ({ 
  x, 
  y, 
  selectedVersionId, 
  onClose 
}) => {
  const handleMenuClick = async (queryName: string) => {
    const params = selectedVersionId ? { version_id: selectedVersionId } : {};
    const success = await copyDQLToClipboard(queryName, params);
    if (success) {
      console.log(`${queryName} をクリップボードにコピーしました`);
    }
    onClose();
  };
  return (
    <div
      style={{
        position: 'fixed',
        top: y,
        left: x,
        backgroundColor: 'white',
        border: '1px solid #ccc',
        borderRadius: '4px',
        padding: '4px',
        boxShadow: '2px 2px 8px rgba(0,0,0,0.2)',
        zIndex: 1000,
        fontSize: '12px',
        minWidth: '180px'
      }}
    >
      <div 
        style={{ 
          padding: '4px 8px', 
          cursor: 'pointer',
          borderBottom: '1px solid #eee'
        }}
        onClick={() => handleMenuClick('list_versions_all')}
      >
        list_versions_all.cypher
      </div>
      <div 
        style={{ 
          padding: '4px 8px', 
          cursor: 'pointer' 
        }}
        onClick={() => handleMenuClick('list_uris_cumulative')}
      >
        list_uris_cumulative.cypher
        {selectedVersionId && <span style={{ color: '#666' }}> (v: {selectedVersionId})</span>}
      </div>
    </div>
  );
};
