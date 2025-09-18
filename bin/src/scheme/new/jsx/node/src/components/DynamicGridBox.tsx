import React from 'react';

interface DynamicGridBoxProps {
  minPosition: number;
  maxPosition: number;
  highlightIndex?: number | null;
}

// 動的なグリッドボックスコンポーネント - 相対位置をサポート（最適化版）
const DynamicGridBox: React.FC<DynamicGridBoxProps> = ({ 
  minPosition, 
  maxPosition, 
  highlightIndex = null 
}) => {
  // 実際に使用する範囲のボックスのみを生成
  const boxCount = maxPosition - minPosition + 1;
  
  return (
    <div style={{
      display: 'flex',
      width: '100%',
      height: '20px'
    }}>
      {Array.from({ length: boxCount }).map((_, i) => {
        // 表示位置に対応する相対位置を計算
        const relativePosition = minPosition + i;
        const isHighlighted = highlightIndex === relativePosition;
        
        return (
          <div
            key={i}
            style={{
              flex: 1,
              height: '100%',
              // 背景色を透明に（親の背景色が見える）
              backgroundColor: isHighlighted 
                ? '#ffeb3b' 
                : 'transparent',
              // ボーダーはハイライト時のみ
              border: isHighlighted 
                ? '2px solid #f57f17'
                : '1px solid rgba(0, 0, 0, 0.05)',
              fontSize: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              // テキスト（番号）はハイライト時のみ表示
              color: isHighlighted ? '#000' : 'transparent'
            }}
          >
            {relativePosition}
          </div>
        );
      })}
    </div>
  );
};

export default DynamicGridBox;
