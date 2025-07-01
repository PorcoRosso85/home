# POC考察：動的settings.json書き換えによる権限制御

## なぜClaude SDKを使うか

### SDKの役割
1. **実際のCLI呼び出し**: 本物のClaude CLIを間接的に実行
2. **セッション管理**: --uriディレクトリでの独立したセッション
3. **ログ記録**: stream.jsonlへの実行ログ保存

### テストで検証できること
1. **settings.json読み込み**: 実際のCLIが設定を読むか
2. **権限制御の動作**: allowedToolsが機能するか
3. **フック実行**: PreToolUse/Stopフックが動くか

## 実証の限界

このPOCが示すのは：
- **基本動作の確認**: settings.jsonによる制御が可能
- **SDKとの統合**: claude_sdkでの動的設定管理
- **実用性の検証**: 実際の開発での利用可能性

ただし：
- **内部実装は不明**: Claude CLIの詳細な動作は分からない
- **エラーメッセージは予測不能**: 実際のエラー内容は変わる可能性
- **SDKの影響**: 直接CLIを使う場合と挙動が異なるかも

## 規約への準拠

CONVENTION.yamlに従い、モックを削除して実際のCLI（SDK経由）を使用：

```typescript
// poc/claude_sdkをラッパーとして使用
const sdkPath = join(Deno.cwd(), "../../claude_sdk/claude.ts");
return ["deno", "run", "--allow-all", sdkPath];
```

これにより、より現実的な動作検証が可能になりました。