// colors.ts - 色定義

// ノードタイプに応じた色
export const nodeTypeColors = {
  '入力': '#3498db',
  '出力': '#2ecc71',
  '処理': '#e74c3c',
  '変換': '#f39c12',
  '検証': '#9b59b6',
  '保存': '#1abc9c',
  '集約': '#34495e',
  '分析': '#95a5a6'
};

// 実装ステータスに応じた色
export const statusColors = {
  '計画中': '#BDC3C7',
  '開発中': '#3498DB',
  'テスト中': '#F39C12',
  '完了': '#2ECC71',
  '廃止予定': '#E74C3C',
  '再設計中': '#9B59B6'
};

// 進捗バーの色を取得する関数
export const getProgressColor = (progress: number): string => {
  if (progress < 30) return '#ef4444';
  if (progress < 70) return '#f59e0b';
  return '#10b981';
};

// 実装ステータスに応じた色とスタイルを取得する関数
export const getStatusStyle = (status: string) => {
  let bgColor = '#f3f4f6';
  let textColor = '#1f2937';
  
  switch (status) {
    case '完了': 
      bgColor = '#d1fae5'; 
      textColor = '#065f46';
      break;
    case 'テスト中': 
      bgColor = '#fef3c7'; 
      textColor = '#92400e';
      break;
    case '開発中': 
      bgColor = '#dbeafe'; 
      textColor = '#1e40af';
      break;
    case '計画中': 
      bgColor = '#f3f4f6'; 
      textColor = '#1f2937';
      break;
    case '廃止予定': 
      bgColor = '#fee2e2'; 
      textColor = '#b91c1c';
      break;
    case '再設計中': 
      bgColor = '#ede9fe'; 
      textColor = '#5b21b6';
      break;
  }
  
  return {
    background: bgColor,
    color: textColor,
    padding: '2px 8px',
    borderRadius: '9999px',
    fontSize: '12px',
    fontWeight: 500,
    display: 'inline-flex',
    alignItems: 'center'
  };
};
