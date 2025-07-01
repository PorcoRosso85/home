# POC考察：動的settings.json書き換えによる権限制御

## なぜモックでテスト可能か

### モックが証明できること
1. **基本的な読み込み動作**: settings.jsonファイルの存在確認と読み込み
2. **権限チェックロジック**: allowedToolsによる単純な権限制御
3. **フック実行フロー**: PreToolUse/PostToolUse/Stopのタイミング

### モックでは証明できないこと
1. **実際のClaude CLIの内部実装**: 本物のsettings.json読み込みタイミング
2. **複雑なフック動作**: JSONパイプライン、並列実行、タイムアウト処理
3. **完全な権限システム**: allowedToolsの実際の実装詳細

## 実証の意味

このPOCが示すのは：
- **概念実証**: 動的権限制御が**理論的に可能**であること
- **インターフェース確認**: settings.jsonの構造と期待される動作
- **SDKとの統合可能性**: claude_sdkでの活用方法

完全な証明には実際のClaude CLIでのテストが必要ですが、
基本的な動作原理の確認には十分です。

## 規約への準拠

CONVENTION.yamlの「モックよりも実際の値を使用」に従い、
test_utils.tsで実際のCLIを優先的に使用する仕組みを実装しました。

```typescript
// 実際のCLIがあれば使用、なければモック
const claudeCmd = await getClaudeCommand();
```

これにより、将来的に実際のClaude CLIでテストする際も
テストコードの変更なしに移行できます。