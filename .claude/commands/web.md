※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# web
/web

# 説明
readabilityを使用してウェブドキュメントを取得する。保存先ディレクトリが指定された場合のみダウンロード・保存を行う。

# 実行内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
## URLのみ指定した場合
```
/web https://example.com/article
```
1. エラー表示：「保存先の指定が必要です。使用例: /web https://example.com/article ~/bin/src/poc/web/」
2. WebFetchなど他のツールの使用は禁止
3. ユーザーに指示を仰ぐ：「保存先を指定してコマンドを再実行するか、別の方法をご指示ください」

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