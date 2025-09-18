# Bun Vessel Implementation

## Overview

Bun版のVesselシステムは、JavaScriptとTypeScriptの動的実行を可能にする「器」です。Bunの高速起動とTypeScriptネイティブサポートを活かした実装です。

## 実装済みのVessels

### 1. vessel.ts - JavaScript実行器
```bash
echo 'console.log("Hello")' | bun vessel.ts
```
- JavaScriptコードを標準入力から受け取り実行
- async/awaitをサポート
- エラー時は適切に終了コード1を返す

### 2. vessel_ts.ts - TypeScript実行器
```bash
echo 'const x: string = "TypeScript!"; console.log(x)' | bun vessel_ts.ts
```
- TypeScript型注釈を含むコードを実行
- 一時ファイル経由でBunのTypeScriptトランスパイルを活用
- インターフェースや型定義をサポート

### 3. vessel_data.ts - データ認識型実行器
```bash
echo "5" | bun vessel_data.ts 'console.log(parseInt(data) * 2)'
```
- 前段の出力を`data`変数として受け取る
- コマンドライン引数でスクリプトを指定

## パイプラインの例

### JavaScript パイプライン
```bash
# 数値を生成 → 2倍 → 結果
echo 'console.log(5)' | bun vessel.ts | \
bun vessel_data.ts 'console.log(parseInt(data) * 2)'
# 出力: 10
```

### TypeScript パイプライン
```bash
# 型付きデータ生成 → 型安全な処理
bun vessel_ts.ts < generate_products.ts | \
bun vessel_data_ts.ts 'process_products_with_types.ts'
```

## 特徴

1. **高速起動** - Bunの起動速度により、パイプライン処理が高速
2. **TypeScriptサポート** - 型注釈を保持したまま実行可能
3. **Bun特有機能** - `Bun.$`によるシェルコマンド統合
4. **エラー伝播** - パイプライン中のエラーを適切に処理

## Python版との違い

| 特徴 | Python版 | Bun版 |
|------|----------|-------|
| 起動速度 | 遅い | 高速 |
| 型サポート | なし | TypeScript |
| 非同期 | asyncio | ネイティブ |
| エコシステム | 巨大 | 成長中 |

## 使い分け

- **Bun版を使う場合**：
  - 高速な起動が必要
  - TypeScriptの型安全性が欲しい
  - モダンなJavaScript機能を使いたい

- **Python版を使う場合**：
  - 機械学習ライブラリが必要
  - より柔軟な動的実行が必要
  - 既存のPythonエコシステムと統合