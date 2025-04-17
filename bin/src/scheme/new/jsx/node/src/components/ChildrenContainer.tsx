import React, { ReactNode } from 'react';

interface ChildrenContainerProps {
  children: ReactNode;
}

// 子ノードコンテナコンポーネント
const ChildrenContainer: React.FC<ChildrenContainerProps> = ({ children }) => {
  return (
    <div style={{
      marginTop: '5px',
      paddingLeft: '20px'
    }}>
      {children}
    </div>
  );
};

export default ChildrenContainer;
