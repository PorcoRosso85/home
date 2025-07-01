# Claude Settings Dynamic Permission Control POC

## 概要

Claude Codeのsettings.jsonを動的に書き換えることで、実行時の権限制御を実現するPOC。
`poc/claude_sdk`をラッパーとして使用し、実際のClaude CLIの動作を検証。

## 実証内容

1. **動的権限制御**: settings.jsonのallowedToolsを変更することで、使用可能なツールを制限
2. **フック実行確認**: PreToolUse/PostToolUse/Stopフックが正しく実行されることを確認
3. **設定の即時反映**: 新しいClaude Codeプロセスごとに設定が読み込まれることを利用

## TDD Redアプローチ

失敗するテストを先に作成し、実装なしで動作を確認：

```bash
# Nix環境に入る
nix develop

# TDD Red phaseのテストを実行（失敗が期待される）
nix run .#test-red

# または個別に実行
deno test --allow-all --filter=permission  # 権限制御テスト
deno test --allow-all --filter=hook       # フック実行テスト
```

## テストケース

### 1. 権限制御テスト (`settings_permission_test.ts`)

- 読み取り専用モードでWriteツールがブロックされる
- 権限昇格フラグで書き込みが可能になる
- settings.jsonの動的更新が反映される

### 2. フック実行テスト (`hook_execution_test.ts`)

- PreToolUseフックが実行される
- 設定ごとに異なるフックが実行される
- フックによるツール使用のブロック

## Claude SDKとの連携

`poc/claude_sdk`をラッパーとして使用：

- `--claude-id`: セッション識別子
- `--uri`: 作業ディレクトリ（settings.jsonの配置場所）
- `--allow-write`: 書き込み権限フラグ
- Claude SDKが実際のClaude CLIを呼び出し

## 実際の使用例

SDKでの動的設定注入：

```typescript
// 実行前に設定を書き込み
const settings = {
  allowedTools: ["Read", "Glob"],  // 読み取り専用
  hooks: {
    PreToolUse: [{
      matcher: ".*",
      hooks: [{
        type: "command",
        command: "echo 'Tool: '$(jq -r .tool_name)' at '$(date) >> audit.log"
      }]
    }]
  }
};

await Deno.writeTextFile(
  `${workdir}/.claude/settings.json`,
  JSON.stringify(settings, null, 2)
);

// Claude実行
const cmd = new Deno.Command("claude", {
  cwd: workdir,
  // ...
});
```

## テストの意味

### 検証内容
- **settings.jsonの読み込み**: Claude CLIが実際に設定ファイルを読むか
- **権限制御**: allowedToolsが機能するか
- **フック実行**: PreToolUse/Stopフックが動作するか

### 制限事項
- **完全な証明ではない**: 実際のClaude CLIの内部実装詳細は不明
- **SDK経由の影響**: claude_sdkが間に入ることの影響
- **エラーメッセージの不確実性**: 実際のエラー内容は予測できない

## 結論

- settings.jsonは**実行ごとに読み込まれる**ため、動的な権限制御が可能
- モックは**基本動作の検証**には十分だが、**完全な証明には実際のCLIが必要**
- フックシステムと組み合わせることで、高度な制御とロギングが実現可能
- SDKレイヤーでの設定管理により、実行コンテキストごとの権限分離が可能