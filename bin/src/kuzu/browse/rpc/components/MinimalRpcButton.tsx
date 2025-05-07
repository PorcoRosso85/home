import React from 'react';
import * as logger from '../../../common/infrastructure/logger';

/**
 * 最小構成のRPCデバッグボタン - コンソール表示のみ
 */
const MinimalRpcButton: React.FC = () => {
  const handleClick = async () => {
    console.log('===== ボタンがクリックされました =====');
    logger.info('ボタンがクリックされました', { time: new Date().toISOString() });
    
    // LSコマンド実行（POSTリクエストのみ使用）
    try {
      logger.info('LSコマンド実行リクエスト送信...');
      
      const response = await fetch('http://localhost:8000/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 'test-' + Date.now(),
          method: 'execute',
          params: { command: 'ls', args: ['-la'] }
        })
      });
      
      console.log('LS実行ステータス:', response.status);
      const text = await response.text();
      logger.info('LS実行結果', { status: response.status, result: text });
    } catch (error) {
      logger.error('LS実行エラー', error);
    }
  };
  
  return (
    <button
      onClick={handleClick}
      style={{
        padding: '8px 16px',
        backgroundColor: '#4caf50',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      LS実行（コンソール）
    </button>
  );
};

export default MinimalRpcButton;
