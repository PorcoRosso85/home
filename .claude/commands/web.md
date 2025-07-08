# web
/web

# 説明
readabilityを使用してウェブドキュメントを取得する。保存先ディレクトリが指定された場合のみダウンロード・保存を行う。

# 実行内容
## URLのみ指定した場合（ダウンロードなし）
```
/web https://example.com/article
```
1. nix run でreadabilityを実行してコンテンツを表示
2. ファイルは保存しない

## URL + 保存先を指定した場合
```
/web https://example.com/article ~/bin/src/poc/web/
```
1. nix run でreadabilityを実行
2. 指定ディレクトリにMarkdown形式で保存
3. ファイル名: YYYY-MM-DD_HH-MM-SS_ドメイン名_slug.md
4. 保存したファイルパスを返す

## キャッシュ検索モード
```
/web search キーワード 検索ディレクトリ
```
1. 指定ディレクトリ内のキャッシュを検索
2. 見つかったドキュメントのリストを表示

# 保存形式
```markdown
---
url: https://example.com/article
saved_at: 2025-06-29T12:00:00Z
title: Article Title
domain: example.com
---

[記事の本文]
```

# 使用ツール
- nix run /home/nixos/bin/src/poc/readability -- --format md
- メタデータはフロントマターとして追加

# 他コマンドとの連携
- /poc: POC作成時にこのコマンドを使用してドキュメントを取得
- /crawl: 要求されたときに指定URL配下を再帰的にすべて取得するためのURL配列機能