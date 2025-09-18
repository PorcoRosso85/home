# requirement_diff

要件DB内URIとファイルシステムの差分検出

## フロー
```bash
# KuzuDBからURI取得→diffへパイプ→プロジェクトディレクトリ渡す
kuzu_query "MATCH (r) RETURN r.uri" | nix run . -- /project
```

## ケース
- 要件先行: missing（要件あり実装なし）→実装対象
- 実装先行: unspecified（実装あり要件なし）→要件後付け