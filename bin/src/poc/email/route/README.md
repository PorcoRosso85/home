# Email Worker POC

## 概要

Cloudflare Email Workersを使用した、純粋なメールルーティング処理のPOC実装。

## 目的

- Email Workersの基本的な動作確認
- メールのフィルタリング・ルーティングロジックの実装
- forward/rejectの判定処理のテスト
- Cloudflare Email Routing APIの理解

## アーキテクチャ

```
┌─────────────┐    ┌──────────────────┐    ┌─────────┐
│  外部送信者  │───>│ Cloudflare Email │───>│ Worker  │
└─────────────┘    │    Routing       │    └─────────┘
                   └──────────────────┘         │
                                                 ├─── forward() ──> 受信箱
                                                 └─── reject()  ──> 拒否
```

## 実装要素

### 1. Email Routing設定
- カスタムドメインのメール受信設定
- Worker へのルーティングルール

### 2. Email Worker
- メール受信イベントのハンドリング
- フィルタリングロジック（allowlist/blocklist）
- forward/rejectの判定
- カスタムルーティングルール

## ForwardableEmailMessage API

Email Workerが受け取るメッセージオブジェクト：

```typescript
type ForwardableEmailMessage = {
  from: string;                    // 送信元アドレス
  to: string;                      // 宛先アドレス
  headers: Headers;                // メールヘッダー
  raw: () => Promise<ArrayBuffer>; // 生メールデータ取得
  setReject: (reason: string) => void;                     // メール拒否
  forward: (to: string, headers?: Headers) => Promise<void>; // メール転送
}
```

## 実装ステップ

1. Cloudflare アカウントでEmail Routingを有効化
2. Email Worker の実装
3. Wranglerでのローカルテスト
4. Worker のデプロイ
5. Email Routingルールの設定
6. テストメールでの動作確認

## 制限事項

- Email Routing の最大メールサイズ: 25MB
- Worker の実行時間制限: 30秒（有料プランで延長可能）
- 1日あたりのメール処理数制限あり

## 今後の拡張案

- 複雑なフィルタリングルール
- 条件付き転送ロジック
- メールヘッダーの書き換え
- 複数宛先への転送
- スパム判定との連携

## 実装詳細

### Worker実装の要点

```typescript
// Email Workerの基本構造
export default {
  async email(message: ForwardableEmailMessage, env: Env, ctx: ExecutionContext): Promise<void> {
    // フィルタリングロジックの実装
    
    // Example 1: Allowlist
    const allowlist = ["trusted@example.com"];
    if (!allowlist.includes(message.from)) {
      message.setReject("Not in allowlist");
      return;
    }
    
    // Example 2: Blocklist
    const blocklist = ["spam@example.com"];
    if (blocklist.includes(message.from)) {
      message.setReject("Blocked sender");
      return;
    }
    
    // Example 3: Subject filtering
    const subject = message.headers.get("subject") || "";
    if (subject.toLowerCase().includes("spam")) {
      message.setReject("Spam detected");
      return;
    }
    
    // Forward to inbox if all checks pass
    await message.forward("inbox@example.com");
  }
};
```

### wrangler.toml設定

```toml
name = "email-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"

# Email Routingルールの設定（デプロイ後）
[[email_routing_rules]]
type = "all"
actions = [
  { type = "worker", value = "email-worker" }
]
```

## 単一責務の原則

このシステムは「メールルーティング」という単一の責務のみを持つ：

1. **受信メールの判定処理のみ**
   - forward/rejectの判定
   - フィルタリングロジックの実装
   - 保存やアーカイブは行わない

2. **ステートレスな処理**
   - メールごとに独立した判定
   - 状態の保持は行わない

3. **他システムとの独立性**
   - ストレージシステムから独立
   - メール配信後の処理から独立
   - 純粋なルーティング機能のみ提供