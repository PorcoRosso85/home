# Symbol Search Implementation

## 仕様

統一された出力形式でシンボル探索を行うツール

### 入力
- ディレクトリパス: `./path/to/dir`
- URLスキーマ: `file://path/to/file`, `http://example.com/file` (将来拡張)

### 出力形式

```python
SearchResult = {
    "success": bool,
    "data": Optional[List[Symbol]],
    "error": Optional[str],
    "metadata": {
        "searched_files": int,
        "search_time_ms": float,
        # その他のメタ情報
    }
}

Symbol = {
    "name": str,              # シンボル名
    "type": str,              # function, class, method, variable, constant, import, type_alias
    "path": str,              # ファイルパスまたはURL
    "line": int,              # 行番号
    "column": Optional[int],  # 列番号（オプション）
    "context": Optional[str], # コードコンテキスト（オプション）
}
```

### 特徴
- エラーも成功も統一した`SearchResult`形式で返却
- 複数言語対応（拡張可能な設計）
- URLスキーマ対応で将来的な拡張性

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