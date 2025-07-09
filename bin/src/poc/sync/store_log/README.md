# Event Log Persistence

イベントストリーミングのための永続化層。

## 概要

WebSocketサーバーのイベントログを永続化し、サーバー再起動後も継続性を保証します。

## 設計

- **イベントログ形式**: JSONL（JSON Lines）
- **オフセット管理**: Kafkaライクなオフセットベースの読み出し
- **ストリーミング対応**: リアルタイムイベント配信

## 使用方法

```typescript
import { EventLogPersistence } from "./mod.ts";

const log = new EventLogPersistence({
  path: './event-log',
  format: 'jsonl',
  syncWrites: true
});

// イベント追加
const offset = await log.append(event);

// イベント読み出し
const events = await log.readEvents(fromOffset);

// ストリーミング
const stream = log.stream();
```