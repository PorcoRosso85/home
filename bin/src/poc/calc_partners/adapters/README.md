# UIアダプター規約

## 原則
呼び出し側は一切の環境差異を考慮不要とする

## 実装責務

### ink.ts
- Inkコンポーネントの再export
- CLIアプリケーション用

### html.tsx  
- Ink互換APIのHTML実装
- ブラウザアプリケーション用

## 互換性保証

### 必須実装コンポーネント
- `Box`: Flexboxコンテナ
- `Text`: スタイル付きテキスト
- `Newline`: 改行
- `Spacer`: スペース調整（環境差吸収）

### props互換性
同じpropsで同じ視覚的結果を実現する：
- 環境固有の最適化は各アダプター内で完結
- 呼び出し側のコード変更は不要

## 使用方法

```typescript
// CLI版 (cli/Calculator.tsx)
import { Box, Text, Spacer } from '../adapters/ink'

const Calculator = () => (
  <Box>
    <Text>LTV</Text>
    <Spacer />
    <Text>¥3,000</Text>
  </Box>
)

// Browser版 (browser/Calculator.tsx)  
import { Box, Text, Spacer } from '../adapters/html'

const Calculator = () => (
  <Box>
    <Text>LTV</Text>
    <Spacer />
    <Text>¥3,000</Text>
  </Box>
)
```

## 実装ガイドライン

1. **Spacerの扱い**
   - CLI: Inkのデフォルト動作
   - HTML: CSS flexbox で `flex: 1` を実装

2. **スタイリング**
   - CLI: Ink標準props (`color`, `bold`, etc.)
   - HTML: 同等のCSS変換を実装

3. **レイアウト**
   - 両環境でFlexboxモデルを基本とする
   - `flexDirection`, `padding`, `gap` 等を統一

## 制約事項

- 環境固有機能（useInput, exit等）は共通化しない
- 計算・シミュレーション機能に必要な最小セットのみ実装
- 装飾的な機能は実装しない（README.md の絶対禁止事項準拠）