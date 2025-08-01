# Vessel実装規約

Vesselは動的スクリプト実行のための「器」システムです。この規約は、全言語での一貫したVessel実装を保証します。

## 基本原則

1. **標準入出力インターフェース**
   - 入力: 標準入力からスクリプトを受け取る
   - 出力: 標準出力に結果を出力
   - エラー: 標準エラー出力に構造化ログを出力

2. **パイプライン構成可能性**
   ```bash
   vessel | vessel | vessel  # 各段階でスクリプトを実行
   ```

3. **エラー処理**
   - エラー時は終了コード1
   - エラー情報は構造化ログとして標準エラー出力へ

## 実装要件

### 必須コンポーネント

1. **基本vessel** (`vessel.{py,ts}`)
   - 標準入力からスクリプトを読み込み実行
   - 動的実行機能（Python: exec, TypeScript: eval/AsyncFunction）

2. **データ認識vessel** (`vessel_data.{py,ts}`)
   - 前段の出力を`data`変数として受け取る
   - コマンドライン引数でスクリプトを指定

3. **構造化ログ** (`vessel_log.{py,ts}`)
   - JSON形式でログ出力
   - print/console.log の直接使用を禁止

### ログ形式

```json
{
  "timestamp": "2024-01-01T00:00:00.000Z",
  "level": "error|info|debug",
  "vessel_type": "vessel|data|custom",
  "message": "Human readable message",
  "error": "Error details if applicable",
  "error_type": "Error class name"
}
```

### 環境変数

- `VESSEL_DEBUG`: "1", "true", "yes" でデバッグログ有効化

## 言語別実装詳細

### Python
```python
# 実行コンテキスト
context = {
    '__name__': '__main__',
    'vessel': True,
    'print': logger.output  # 構造化ログ対応
}
exec(script, context)
```

### TypeScript/Bun
```typescript
// 非同期実行サポート
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const func = new AsyncFunction(script);
await func();
```

## テスト要件

各vessel実装は以下をテストすること：

1. **基本実行**
   - スクリプトの実行と出力確認
   - 非同期処理のサポート

2. **エラー処理**
   - エラー時の終了コード
   - 構造化エラーログの出力

3. **パイプライン**
   - vessel間でのデータ受け渡し
   - エラー伝播

## 禁止事項

1. **print/console.log の直接使用**
   - 必ず構造化ログシステムを経由すること
   - 例外: テストコード内での使用は許可

2. **グローバル状態の変更**
   - 各実行は独立した環境で行う

3. **同期的なファイルI/O**
   - 標準入出力のみを使用

## 拡張ガイドライン

新しいvessel実装時は：

1. 基本vesselの構造を踏襲
2. 構造化ログシステムを使用
3. テストを追加
4. README_[LANG].md でドキュメント化

## 関連規約

- [error_handling.md](./error_handling.md) - エラー処理の詳細
- [logging.md](./logging.md) - ログ出力の一般規約
- [prohibited_items.md](./prohibited_items.md) - 禁止事項の詳細