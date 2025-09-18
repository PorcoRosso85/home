# CSS-in-JS規約

## 基本方針

外部CSSファイルは一切使用せず、React TSXコンポーネント内でインラインスタイルを使用する。

## 記述規則

### 1. style属性にオブジェクト形式で記述

```tsx
// ✅ 正しい
<div style={{
  padding: '20px',
  maxWidth: '1200px',
  margin: '0 auto'
}}>

// ❌ 禁止: 文字列形式
<div style="padding: 20px">

// ❌ 禁止: className使用
<div className="container">
```

### 2. JavaScriptのキャメルケース記法

```tsx
// ✅ 正しい
<div style={{
  backgroundColor: '#f0f0f0',
  marginTop: '10px',
  borderRadius: '8px',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
}}>

// ❌ 禁止: kebab-case
<div style={{
  'background-color': '#f0f0f0',
  'margin-top': '10px'
}}>
```

### 3. 単位の明示

```tsx
// ✅ 正しい
<div style={{
  width: '100%',      // 文字列で単位含む
  height: 200,        // 数値のみはpx扱い
  opacity: 0.8,       // 単位不要な属性
  flex: 1             // 単位不要な属性
}}>
```

### 4. 動的スタイル

```tsx
// ✅ 正しい: 状態に基づく動的スタイル
<div style={{
  backgroundColor: isActive ? '#007bff' : '#6c757d',
  transform: `translateX(${offset}px)`,
  ...nodeState.styles  // スプレッド演算子で結合
}}>

// ✅ 正しい: 条件付きスタイル
<div style={{
  display: isVisible ? 'block' : 'none',
  ...(isHighlighted && {
    border: '2px solid #ff0000'
  })
}}>
```

## スタイルの再利用

### 1. スタイルオブジェクトの定義

```tsx
// ✅ 正しい: コンポーネント内でスタイル定義
const Component = () => {
  const containerStyle = {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto'
  };
  
  return <div style={containerStyle}>
};

// ✅ 正しい: 型定義
const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '20px',
    maxWidth: '1200px'
  },
  header: {
    fontSize: '24px',
    fontWeight: 'bold'
  }
};
```

### 2. テーマ定数

```tsx
// ✅ 正しい: 共通の値を定数化
const THEME = {
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    danger: '#dc3545'
  },
  spacing: {
    small: '8px',
    medium: '16px',
    large: '24px'
  }
} as const;

// 使用
<div style={{
  backgroundColor: THEME.colors.primary,
  padding: THEME.spacing.medium
}}>
```

## 禁止事項

### 1. 外部CSSファイル

```tsx
// ❌ 禁止
import './styles.css';
import styles from './styles.module.css';
```

### 2. CSS-in-JSライブラリ

```tsx
// ❌ 禁止: styled-components, emotion等
import styled from 'styled-components';
const Button = styled.button`...`;
```

### 3. classNameの使用

```tsx
// ❌ 禁止
<div className="container">
<div className={styles.container}>
```

### 4. Tailwind CSS

```tsx
// ❌ 禁止
<div className="p-4 max-w-screen-xl mx-auto">
```

## パフォーマンス考慮事項

### 1. スタイルオブジェクトのメモ化

```tsx
// ✅ 推奨: 頻繁に再レンダリングされる場合
const Component = ({ color }) => {
  const style = useMemo(() => ({
    backgroundColor: color,
    padding: '20px'
  }), [color]);
  
  return <div style={style}>;
};
```

### 2. 定数化

```tsx
// ✅ 推奨: 不変のスタイルは外部で定義
const STATIC_STYLE = {
  display: 'flex',
  alignItems: 'center'
} as const;

const Component = () => (
  <div style={STATIC_STYLE}>
);
```

## 例外

なし。すべてのスタイリングはこの規約に従う。

## 関連規約

- [module_design.md](./module_design.md): コンポーネント設計
- [design_principles.md](./design_principles.md): 設計原則

## 理由

1. **依存関係の削減**: CSS処理系が不要
2. **型安全性**: TypeScriptによる型チェック
3. **動的スタイル**: JavaScriptの表現力を活用
4. **バンドルサイズ**: CSS-in-JSライブラリのオーバーヘッドなし
5. **予測可能性**: スタイルの影響範囲が明確