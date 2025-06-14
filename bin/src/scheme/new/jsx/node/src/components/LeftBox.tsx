import React from 'react';

interface LeftBoxProps {
  path: string;
  name: string;
  backgroundColor: string;
}

// 左側ボックスコンポーネント
const LeftBox: React.FC<LeftBoxProps> = ({ path, name, backgroundColor }) => {
  // パスに:::がある場合は関数表示モードを使用
  const isFunction = path.includes(':::');
  
  let displayName = name;
  let displayPath = path;
  
  if (isFunction) {
    // 関数の場合、パスから関数名を抽出
    const parts = path.split(':::');
    const filePath = parts[0];
    const functionName = parts[1];
    
    // 表示用の名前と情報を設定
    displayName = functionName || name;  // パスから関数名を取得、なければ渡された名前を使用
    displayPath = filePath;  // ファイルパスだけを表示
  }
  
  return (
    <div style={{
      backgroundColor: backgroundColor, // 親要素の背景色を使用
      padding: '5px 10px',
      flex: '1',
      borderRadius: '4px 0 0 4px',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }}>
      <span style={{ fontWeight: 'bold' }}>{displayName}</span>
      <span style={{ fontSize: '0.8em', color: '#666', marginLeft: '8px' }}>{displayPath}</span>
    </div>
  );
};

export default LeftBox;
