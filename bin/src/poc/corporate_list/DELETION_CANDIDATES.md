# 削除候補ファイル一覧 (Step 5 Complete)

## 説明
Step 5の完了により、以下のファイルは新パッケージ (scraper-core, scraper-prtimes) に置き換えられました。
段階的な移行のため、現在は削除可能ですが、慎重に進めることを推奨します。

## 削除可能なファイル

### 旧実装コード
- `src/domain/scraper-factory.ts` - ScraperFactory → createPRTimesScraperに置き換え
- `src/domain/scrapers/prtimes-scraper.ts` - packages/scraper-prtimes/src/scraper.tsに移行
- `src/domain/scraper.ts` - packages/scraper-core/src/scraper/base.tsに移行
- `src/domain/extractor.ts` - packages/scraper-prtimes/src/parser.tsに移行
- `src/domain/types.ts` - packages/scraper-core/src/types.tsに移行

### 旧テスト（参照系のみ）
- `test/domain/scraper.test.ts` - 旧実装のテスト（新実装でカバー済み）
- `test/domain/extractor.test.ts` - parser.test.tsで代替済み

## 削除前チェック項目
1. [ ] `bun test` で全テストが通ることを確認
2. [ ] `bun test test/golden-master.test.ts` で120記事取得が維持されていることを確認
3. [ ] `bun run src/main.ts` の実行結果を確認

## 削除コマンド例
```bash
# 段階的削除（推奨）
rm src/domain/scraper-factory.ts
rm src/domain/scrapers/prtimes-scraper.ts
rm src/domain/scraper.ts
rm src/domain/extractor.ts

# 最後に削除
rm src/domain/types.ts

# テストファイル削除
rm test/domain/scraper.test.ts
rm test/domain/extractor.test.ts

# 空ディレクトリ削除
rmdir src/domain/scrapers
rmdir src/domain
rmdir test/domain
```

## 注意事項
- 削除前に必ずバックアップを取ること
- 段階的に削除し、各ステップでテストを実行すること
- src/domain/types.tsは最後に削除（他のファイルで参照されている可能性）

## 移行完了の確認
- [x] workspace設定の追加
- [x] 新パッケージからの実装使用
- [x] テスト結果の維持（120記事）
- [x] インターフェーステストの実装化
- [x] 型定義の新パッケージ移行