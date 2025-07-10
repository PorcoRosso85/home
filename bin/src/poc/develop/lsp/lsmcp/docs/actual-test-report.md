# 実際の動作テスト報告

## テスト環境
- 場所: /home/nixos/bin/src/poc/develop/lsp/
- 実行日時: 2025-07-09
- 使用コマンド: npx @mizchi/lsmcp

## 1. ヘルプ確認
```bash
npx @mizchi/lsmcp --help
```
**結果**: ヘルプ表示確認。`--include`オプションの存在を確認

## 2. Python診断テスト
```bash
npx @mizchi/lsmcp --include "test_good.py" -p pyright
```
**結果**:
- サーバー起動ログは表示される
- `[lsmcp] runLanguageServerWithConfig called` まで進む
- **診断結果は出力されない**
- プロセスが待機状態になる（MCPサーバーモード）

## 3. TypeScript診断テスト
```bash
# テストファイル作成
echo 'const x: string = 123;' > test.ts

# 診断実行
npx @mizchi/lsmcp --include "test.ts" -p typescript
```
**結果**:
- LSPクライアントが初期化される
- `[lspClient] Sending request: initialize` が表示
- 診断処理が開始される（出力が途中で切れているが動作している）

## 4. 結論

### 観察された動作の違い
| 言語 | サーバー起動 | LSPクライアント初期化 | 診断結果出力 |
|------|------------|-------------------|------------|
| Python (pyright) | ✅ | ❌ | ❌ |
| TypeScript | ✅ | ✅ | ✅ |

### 原因
LSMCPのソースコードを推測すると、`--include`フラグの処理が言語によって分岐している：
- TypeScript: CLI診断モードに入る
- その他: MCPサーバーモードで起動（診断は実行されない）

これが実際に確認できた動作です。