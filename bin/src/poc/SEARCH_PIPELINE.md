# Search Pipeline POCs

ディレクトリ検索システムをUnixパイプラインで構築する3つのPOC

## 概要

```bash
# 完全なパイプライン
universal-ctags -R --output-format=json . | \
  search_functions | \
  search_diffs | \
  build_diffs
```

## POC一覧

### 1. search_functions
**責務**: ctagsのコード解析結果 → ユニークなディレクトリパスのリスト

```bash
# コードを含むディレクトリのみ抽出
ctags --output-format=json -R . | search_functions
```

### 2. search_diffs  
**責務**: 前回と今回のディレクトリリスト → 追加/削除されたパスの差分情報

```bash
# 差分検出と状態管理
find . -type d | search_diffs --state-file=.dirstate
```

### 3. build_diffs
**責務**: ディレクトリの追加/削除情報 → KuzuDBインデックスの差分更新

```bash
# インデックス更新
echo "+ src/new" | build_diffs --db-path=search.db
```

## 設計思想

1. **単一責務** - 各ツールは1つのことを上手くやる
2. **テキストストリーム** - 標準入出力で連携
3. **組み合わせ可能** - 他のUnixツールとも連携

## 使用例

### 初回構築
```bash
find . -type d | build_diffs --init
```

### コードディレクトリのみインデックス
```bash
universal-ctags -R --output-format=json . | \
  search_functions | \
  build_diffs --init
```

### 差分更新
```bash
find . -type d | search_diffs | build_diffs
```

## 今後の拡張

- FTS/VSS検索の実装
- メタデータ（README内容）の追加
- 検索インターフェースの作成