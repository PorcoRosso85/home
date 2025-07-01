# Claude Orchestra - Integration Testing POC

## 概要

複数のClaude POC（config, sdk, settings）を組み合わせた統合動作を検証するPOC。
個別には動作するコンポーネントが、実際に連携して期待通りに動作するかをE2Eテストで確認。

## 責務

**複数のClaude POCを組み合わせた統合動作の検証**

- 設定生成から実行までのパイプライン動作
- 権限制御の実効性
- エラーの適切な伝播

## テストシナリオ

### 1. 読み取り専用シナリオ
```
config(readonly) → sdk実行 → Writeツール拒否
```

### 2. 本番環境シナリオ
```
config(production) → settings.json生成 → 危険コマンドブロック
```

### 3. 開発環境シナリオ
```
config(development) → すべてのツール許可
```

### 4. エラー伝播シナリオ
```
config(invalid) → エラー → パイプライン中断
```

## 実行方法

### テスト実行

```bash
# Nixコマンド
nix run .#test
```

### 開発環境

```bash
# 開発シェル起動
nix develop
```

## 依存関係

- `claude_config`: 設定生成POC
- `claude_sdk`: SDK実行POC
- `claude_settings`: settings.json動的生成POC（間接的に使用）

## なぜ必要か

1. **結合部分のバグ発見**: 個別POCの出力と入力の不一致を検出
2. **実使用シナリオ**: ユーザーが実際に使う流れを検証
3. **リグレッション防止**: 個別POC変更時の影響を早期発見

## ドキュメント

- [統合動作例](./INTEGRATION_EXAMPLES.md) - 実際の権限制御の動作確認方法
- [テスト結果](./TEST_RESULTS.md) - 統合テストの実行結果と詳細
- [Claude Config使用例](../claude_config/USAGE_EXAMPLES.md) - 設定パイプラインの詳細な使い方