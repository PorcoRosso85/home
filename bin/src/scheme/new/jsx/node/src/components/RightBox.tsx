import React from 'react';
import DynamicGridBox from './DynamicGridBox';
import { HighlightDataType } from '../types';

interface RightBoxProps {
  isFunction: boolean;
  highlightIndex?: number;
  backgroundColor: string;
  highlightData?: HighlightDataType;
}

// 右側ボックスコンポーネント
const RightBox: React.FC<RightBoxProps> = ({ 
  isFunction, 
  highlightIndex, 
  backgroundColor, 
  highlightData 
}) => {
  // デバッグ用
  React.useEffect(() => {
    if (isFunction && highlightData) {
      console.log(`RightBox: isFunction=${isFunction}, highlightIndex=${highlightIndex}`);
      if (highlightIndex === undefined) {
        console.warn("警告: ハイライトインデックスが未定義です");
      }
    }
  }, [isFunction, highlightIndex, highlightData]);

  return (
    <div style={{
      backgroundColor: backgroundColor, // 親要素の背景色を使用
      padding: '5px 10px',
      width: '480px',
      textAlign: 'left',
      borderRadius: '0 4px 4px 0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-start'
    }}>
      {isFunction && highlightData && typeof highlightData._minPosition === 'number' && (
        <DynamicGridBox 
          minPosition={highlightData._minPosition} 
          maxPosition={highlightData._maxPosition} 
          highlightIndex={highlightIndex} 
        />
      )}
      {isFunction && highlightData && highlightIndex !== undefined && (
        <div style={{ marginLeft: '5px', fontSize: '10px', color: '#666' }}>
          Position: {highlightIndex}
        </div>
      )}
    </div>
  );
};

export default RightBox;
