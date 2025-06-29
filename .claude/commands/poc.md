# poc
/poc

# 説明
ドキュメントをreadabilityで取得し、POCディレクトリに永続化する

# 実行内容
## URLが指定された場合
```
/poc https://example.com/article
```
1. npx @mizchi/readabilityでURLのコンテンツを取得
2. Markdown形式で保存
3. POCディレクトリに日付とタイトルで整理して保存
   - 例: ~/bin/src/poc/2025-06-29_article-title.md

## 探索モードの場合
```
/poc
```
または
```
/poc search キーワード
```
1. ドキュメントの探索支援
2. 見つかったURLに対して保存処理

# POCディレクトリ
- デフォルト: ~/bin/src/poc/
- 初回実行時に確認し、CLAUDE.mdに保存

# 保存形式
```markdown
---
url: https://example.com/article
saved_at: 2025-06-29T12:00:00Z
title: Article Title
---

[記事の本文]
```

# 使用ツール
- npx @mizchi/readability --format md
- メタデータはフロントマターとして追加