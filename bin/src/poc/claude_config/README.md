# Claude Config Pipeline POC

## 概要

Claude Codeの設定を前処理するUnixパイプライン型ツール。
標準入力からタスク情報を受け取り、適切な権限設定とsettings.jsonを生成します。

## 設計思想

- **単一責務**: 設定生成に特化
- **パイプライン対応**: 標準入出力でJSON通信
- **独立性**: claude_sdk等の他POCとは独立動作

## 使用方法

### 1. スタンドアロン実行

```bash
# 読み取り専用モード
echo '{"prompt": "コードレビュー", "mode": "readonly"}' | ./src/config.ts

# 開発モード
echo '{"prompt": "バグ修正", "mode": "development"}' | ./src/config.ts

# 本番モード（危険な操作を制限）
echo '{"prompt": "デプロイ", "mode": "production"}' | ./src/config.ts
```

### 2. パイプライン連携

```bash
# claude_sdkと連携
echo '{"prompt": "タスク", "mode": "readonly"}' | 
  ./src/config.ts | 
  ../claude_sdk/claude.ts

# jqで加工
cat task.json |
  jq '.mode = "production"' |
  ./src/config.ts |
  tee config-output.json
```

### 3. Nix経由

```bash
# 開発環境
nix develop

# 設定生成ツール実行
nix run .#config -- < input.json

# サンプル実行
nix run .#example-readonly
```

## 入出力仕様

### 入力 (ConfigInput)

```json
{
  "prompt": "実行するタスク",
  "mode": "readonly" | "development" | "production",
  "env": {
    "CUSTOM_VAR": "value"
  },
  "workdir": "/path/to/work"
}
```

### 出力 (ConfigOutput)

```json
{
  "prompt": "実行するタスク",
  "workdir": "/path/to/work",
  "claudeId": "readonly-1234567890",
  "sdkOptions": {
    "allowedTools": ["Read", "Glob", "Grep", "LS"],
    "permissionMode": "default"
  },
  "settingsPath": "/path/to/work/.claude/settings.json"
}
```

## プリセット

### readonly
- 読み取り専用ツールのみ許可
- 安全なコードレビューや調査に最適

### development
- すべてのツールを許可
- デバッグ情報を有効化
- 開発作業に最適

### production
- 破壊的な操作を禁止（rm, dd等）
- /etcへの書き込みを防止
- 本番環境での作業に最適

## テスト

```bash
# テストの実行（TDD Green ✓ - すべてのテストが成功）
deno test --allow-all

# または
nix run .#test-red

# 実行結果：6/6 テスト成功
```

## なぜ独立したツールか

1. **Unix哲学**: 一つのことをうまくやる
2. **組み合わせ可能**: 他のツールとパイプで連携
3. **テスト容易**: 入出力が明確でテストしやすい
4. **再利用性**: 必要な部分だけ使える

## 今後の拡張

- カスタムプリセットの読み込み
- より細かい権限制御
- フック設定の動的生成
- 環境別設定の外部化