# Requirement Coverage Analysis Pipeline

要件（KuzuDB）と実装（ファイルシステム）の差分を分析し、シンボル情報で補強するパイプライン。

## ツール構成

1. **kuzu_query.py** - KuzuDBからLocationURIを抽出
2. **diff.nu** - 要件URIとファイルシステムを比較
3. **pipeline.nu** - 全体を統合し、シンボル情報を追加

## 使用方法

### 基本的な使用
```bash
# READMEを表示（デフォルト）
nix run .

# 要件カバレッジ分析
nix run . -- analyze /path/to/project

# シンボル情報付き分析
nix run . -- analyze /path/to/project --show-symbols

# 実装されていない要件のみ表示
nix run . -- analyze req_only /path/to/project

# 要件にない実装のみ表示
nix run . -- analyze impl_only /path/to/project
```

### 個別ツールの使用
```bash
# LocationURI取得
nix run .#kuzu-query

# ファイル差分
echo '[{"uri":"file:///path/to/file"}]' | nix run .#diff -- /path/to/project

# 開発環境
nix develop
```

## 出力形式

```json
[
  {
    "path": "/path/to/file",
    "requirement_exists": true,
    "implementation_exists": false,
    "symbols_count": 10,  // --show-symbolsの場合
    "symbol_types": {     // --show-symbolsの場合
      "function": 5,
      "class": 2,
      "variable": 3
    }
  }
]
```

### フィールドの意味：
- `requirement_exists: true, implementation_exists: false` → 要件のみ（req_only）
- `requirement_exists: false, implementation_exists: true` → 実装のみ（impl_only）

## パイプライン詳細

```
KuzuDB → LocationURI[] → diff → req_only/impl_only files
                              ↓ (--show-symbols)
                         search → symbols
                              ↓
                      統合結果 (JSON)
```

## 依存関係

- requirement/graph - KuzuDB接続
- poc/implementation/search - シンボル検索