# kuzu/browse E2Eテスト

## E2Eテストの意義

E2E（End-to-End）テストは、実際のユーザーの操作をシミュレートし、システム全体の統合動作を確認するテストです。

### 基本原則

1. **UI操作のみ**: Puppeteerを使用してブラウザ経由でUIを操作
2. **バックエンド直接アクセス禁止**: WebSocket、DB、ファイルシステムへの直接接続は行わない
3. **ユーザー視点**: 実際のユーザーが行う操作（クリック、入力、表示確認）のみを実行

### ディレクトリ構成

```
test/e2e/
├── main.ts                 # テストランナー
├── tests/
│   ├── basicTest.ts       # 基本動作テスト
│   └── mergeConflictTest.ts # merge/conflictフローテスト
├── fixtures/              # テストデータ（必要に応じて）
└── README.md             # このファイル
```

### テストカテゴリ

- **basic**: アプリケーション起動、UI表示、接続状態表示
- **merge-conflict**: conflict検出、worktree操作、LLM解決、merge実行

### 実行方法

```bash
# 前提条件
# 1. Viteサーバー起動
cd /home/nixos/bin/src/kuzu/browse
deno run -A build.ts

# 2. RPCサーバー起動（UIが依存する場合）
cd /home/nixos/bin/src/rpc
deno run -A main.ts

# 3. E2Eテスト実行
cd /home/nixos/bin/src/kuzu/browse/test/e2e
deno run -A main.ts
```

### 注意事項

- モック実装はサーバー側で行う（E2Eテスト側では行わない）
- テストケースはUIの実装に合わせて更新する
- セレクタ（data-testid等）は実際のUI実装に合わせる
