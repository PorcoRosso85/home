# Symbol Search Tool (Nushell + ctags)

## 概要
ctagsを使用してコードベース内のシンボル（関数、クラス、メソッド等）を検索するツール。

## 使用方法

```bash
# ファイルまたはディレクトリを検索
nix run . -- path/to/search

# 特定の拡張子でフィルタ
nix run . -- path/to/search --ext py

# 開発環境
nix develop
```

## 出力形式
JSON形式で出力：
```json
{
  "symbols": [
    {
      "name": "シンボル名",
      "type": "class|function|method|variable|constant|unknown",
      "path": "ファイルパス",
      "line": 行番号,
      "column": null,
      "context": null
    }
  ],
  "metadata": {
    "searched_files": 検索ファイル数,
    "search_time_ms": 実行時間
  }
}
```

## パイプライン統合
```bash
# 他のツールと組み合わせ
nix run . -- . | jq '.symbols | map(select(.type == "function"))'
```