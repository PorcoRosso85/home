import React, { useState } from 'react';
import { RpcDebugPanel } from '../../../rpc';

/**
 * RPCデバッグパネルを開くためのボタンコンポーネント
 */
const RpcDebugButton: React.FC = () => {
  const [showPanel, setShowPanel] = useState(false);
  
  const togglePanel = () => {
    setShowPanel(!showPanel);
  };
  
  return (
    <>
      <button
        onClick={togglePanel}
        style={{
          padding: '8px 16px',
          backgroundColor: showPanel ? '#ff9800' : '#4caf50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          fontSize: '14px',
          marginLeft: '10px'
        }}
      >
        <span style={{ fontSize: '18px' }}>🔧</span>
        {showPanel ? 'パネルを閉じる' : 'RPCデバッグ'}
      </button>
      
      {showPanel && (
        <div style={{
          position: 'fixed',
          top: '0',
          left: '0',
          right: '0',
          bottom: '0',
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '20px',
            width: '80%',
            maxWidth: '800px',
            maxHeight: '90%',
            overflow: 'auto',
            position: 'relative'
          }}>
            <button
              onClick={togglePanel}
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer'
              }}
            >
              ×
            </button>
            <RpcDebugPanel />
          </div>
        </div>
      )}
    </>
  );
};

export default RpcDebugButton;
