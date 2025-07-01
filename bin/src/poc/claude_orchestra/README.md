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

```bash
# 開発環境
nix develop

# TDD Red フェーズ（失敗するテスト）
nix run .#test-red

# 個別テスト
deno test --allow-all
```

## 依存関係

- `claude_config`: 設定生成POC
- `claude_sdk`: SDK実行POC
- `claude_settings`: settings.json動的生成POC（間接的に使用）

## なぜ必要か

1. **結合部分のバグ発見**: 個別POCの出力と入力の不一致を検出
2. **実使用シナリオ**: ユーザーが実際に使う流れを検証
3. **リグレッション防止**: 個別POC変更時の影響を早期発見

## TDD Red フェーズ

現在、すべてのテストは失敗することが期待されています：
- POC間の実際の統合がまだ実装されていない
- パスの解決やプロセス間通信が未実装
- これらの失敗が仕様を明確にする