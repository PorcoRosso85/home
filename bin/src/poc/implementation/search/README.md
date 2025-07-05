# Symbol Search Implementation

## 仕様

統一された出力形式でシンボル探索を行うツール

**bin/docs/conventions 準拠**

### 入力
- ディレクトリパス: `./path/to/dir`
- URLスキーマ: `file://path/to/file`, `http://example.com/file` (将来拡張)

### 出力形式

types.py でTypedDictとして定義：

```python
# 成功時
SearchSuccessDict = {
    "symbols": List[SymbolDict],
    "metadata": MetadataDict
}

# エラー時
SearchErrorDict = {
    "error": str,
    "metadata": MetadataDict
}

SearchResult = SearchSuccessDict | SearchErrorDict
```

**convention準拠ポイント:**
- ジェネリックResult型ではなく、具体的な成功/失敗型
- success/failureフラグを持たない
- エラーを値として返す（raise禁止）

### 設計原則
- エラーを値として返す（raise禁止）
- データと処理を分離（TypedDictでデータ定義）
- 1ファイル1公開機能（search_symbols関数）
- クラスベースOOP禁止

### 対象シンボル
- 関数定義
- クラス定義
- メソッド定義
- 変数定義
- 定数定義
- インポート文
- 型エイリアス

## TDD進行状況
- [x] Red: 失敗するテスト作成
- [ ] Green: 最小限の実装
- [ ] Refactor: リファクタリング