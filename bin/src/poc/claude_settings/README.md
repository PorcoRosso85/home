# Claude Settings Dynamic Permission Control POC

## 概要

Claude Codeのsettings.jsonを動的に書き換えることで、実行時の権限制御を実現するPOC。

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

## モックCLI

`mock_claude.ts`は、Claude Codeの動作を模倣するシンプルなCLI：

- settings.jsonの読み込み
- allowedToolsによる権限チェック
- フックの実行（PreToolUse/Stop）
- exit code 2でのブロック処理

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

## なぜモックでテスト可能か

### モックの役割
- **動作の再現**: settings.json読み込みと権限チェックの基本動作を模倣
- **高速実行**: 実際のClaude CLIより高速にテスト実行可能
- **制御可能**: 確定的な動作でテストの再現性を保証

### モックの限界
- **完全な証明ではない**: 実際のClaude CLIの内部実装とは異なる
- **フック実行の違い**: 実際のフックシステムの複雑な動作は再現できない
- **権限システムの簡略化**: allowedToolsの実際の実装詳細は不明

### 実際のClaude CLIでのテスト

規約（CONVENTION.yaml）に従い「モックよりも実際の値を使用」すべきため、
実際のClaude CLIが利用可能な場合はそちらを使用：

```typescript
// test_utils.tsで自動判定
const claudeCmd = await getClaudeCommand();
// ["claude"] または ["deno", "run", "--allow-all", "mock_claude.ts"]
```

## 結論

- settings.jsonは**実行ごとに読み込まれる**ため、動的な権限制御が可能
- モックは**基本動作の検証**には十分だが、**完全な証明には実際のCLIが必要**
- フックシステムと組み合わせることで、高度な制御とロギングが実現可能
- SDKレイヤーでの設定管理により、実行コンテキストごとの権限分離が可能