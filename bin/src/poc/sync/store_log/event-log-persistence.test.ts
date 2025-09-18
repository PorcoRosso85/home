import { assertEquals, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { EventLogPersistence } from "./mod.ts";
import type { CausalOperation } from "./mod.ts";

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

Deno.test("Event Log Persistence", async (t) => {
  
  await t.step("should append and read events sequentially", async () => {
    const log = new EventLogPersistence({
      path: './test-event-log',
      format: 'jsonl'
    });

    const event1: CausalOperation = {
      id: "op1",
      type: "DDL",
      dependsOn: [],
      payload: { ddlType: "CREATE_TABLE", query: "CREATE NODE TABLE Users (id STRING, PRIMARY KEY(id))" },
      clientId: "client-1",
      timestamp: Date.now()
    };

    const event2: CausalOperation = {
      id: "op2",
      type: "DDL",
      dependsOn: ["op1"],
      payload: { ddlType: "ADD_COLUMN", query: "ALTER TABLE Users ADD name STRING" },
      clientId: "client-1",
      timestamp: Date.now() + 1
    };

    // イベントを追加
    const offset1 = await log.append(event1);
    const offset2 = await log.append(event2);

    assertEquals(offset1, 0, "First event should have offset 0");
    assertEquals(offset2, 1, "Second event should have offset 1");

    // イベントを読み出し
    const events = await log.readEvents();
    assertEquals(events.length, 2, "Should read 2 events");
    assertEquals(events[0].id, "op1");
    assertEquals(events[1].id, "op2");

    // クリーンアップ
    await log.close();
    await Deno.remove('./test-event-log', { recursive: true });
  });

  await t.step("should read events from specific offset", async () => {
    const log = new EventLogPersistence({
      path: './test-event-log',
      format: 'jsonl'
    });

    // 5つのイベントを追加
    for (let i = 0; i < 5; i++) {
      await log.append({
        id: `op${i}`,
        type: "DDL",
        dependsOn: i > 0 ? [`op${i-1}`] : [],
        payload: { ddlType: "CREATE_TABLE", query: `CREATE NODE TABLE T${i} (id STRING, PRIMARY KEY(id))` },
        clientId: "client-1",
        timestamp: Date.now() + i
      });
    }

    // オフセット2から読み出し
    const events = await log.readEvents(2);
    assertEquals(events.length, 3, "Should read 3 events from offset 2");
    assertEquals(events[0].id, "op2");
    assertEquals(events[2].id, "op4");

    // クリーンアップ
    await log.close();
    await Deno.remove('./test-event-log', { recursive: true });
  });

  await t.step("should persist events across server restarts", async () => {
    const logPath = './test-event-log';
    
    // 最初のインスタンス
    const log1 = new EventLogPersistence({
      path: logPath,
      format: 'jsonl'
    });

    await log1.append({
      id: "persist-op1",
      type: "DDL",
      dependsOn: [],
      payload: { ddlType: "CREATE_TABLE", query: "CREATE NODE TABLE Persistent (id STRING, PRIMARY KEY(id))" },
      clientId: "client-1",
      timestamp: Date.now()
    });

    await log1.close();

    // 新しいインスタンス（サーバー再起動シミュレート）
    const log2 = new EventLogPersistence({
      path: logPath,
      format: 'jsonl'
    });

    const events = await log2.readEvents();
    assertEquals(events.length, 1, "Should read persisted event");
    assertEquals(events[0].id, "persist-op1");

    // 追加のイベント
    await log2.append({
      id: "persist-op2",
      type: "DDL",
      dependsOn: ["persist-op1"],
      payload: { ddlType: "ADD_COLUMN", query: "ALTER TABLE Persistent ADD data STRING" },
      clientId: "client-2",
      timestamp: Date.now()
    });

    const allEvents = await log2.readEvents();
    assertEquals(allEvents.length, 2, "Should have 2 events total");

    // クリーンアップ
    await log2.close();
    await Deno.remove(logPath, { recursive: true });
  });

  await t.step("should handle concurrent appends safely", async () => {
    const log = new EventLogPersistence({
      path: './test-event-log',
      format: 'jsonl',
      syncWrites: true // 同期書き込みを強制
    });

    // 並行して複数のイベントを追加
    const promises = [];
    for (let i = 0; i < 10; i++) {
      promises.push(log.append({
        id: `concurrent-${i}`,
        type: "DDL",
        dependsOn: [],
        payload: { ddlType: "CREATE_TABLE", query: `CREATE NODE TABLE C${i} (id STRING, PRIMARY KEY(id))` },
        clientId: `client-${i % 3}`,
        timestamp: Date.now() + i
      }));
    }

    const offsets = await Promise.all(promises);
    
    // オフセットが重複していないことを確認
    const uniqueOffsets = new Set(offsets);
    assertEquals(uniqueOffsets.size, 10, "All offsets should be unique");

    // すべてのイベントが保存されていることを確認
    const events = await log.readEvents();
    assertEquals(events.length, 10, "Should have all 10 events");

    // クリーンアップ
    await log.close();
    await Deno.remove('./test-event-log', { recursive: true });
  });

  await t.step("should get latest offset correctly", async () => {
    const log = new EventLogPersistence({
      path: './test-event-log',
      format: 'jsonl'
    });

    // 初期状態
    let offset = await log.getLatestOffset();
    assertEquals(offset, -1, "Empty log should return -1");

    // イベント追加後
    await log.append({
      id: "offset-test",
      type: "DDL",
      dependsOn: [],
      payload: { ddlType: "CREATE_TABLE", query: "CREATE NODE TABLE Test (id STRING, PRIMARY KEY(id))" },
      clientId: "client-1",
      timestamp: Date.now()
    });

    offset = await log.getLatestOffset();
    assertEquals(offset, 0, "Should return 0 after first event");

    // さらに追加
    for (let i = 1; i < 5; i++) {
      await log.append({
        id: `offset-test-${i}`,
        type: "DDL",
        dependsOn: [],
        payload: { ddlType: "CREATE_TABLE", query: `CREATE NODE TABLE Test${i} (id STRING, PRIMARY KEY(id))` },
        clientId: "client-1",
        timestamp: Date.now() + i
      });
    }

    offset = await log.getLatestOffset();
    assertEquals(offset, 4, "Should return 4 after 5 events");

    // クリーンアップ
    await log.close();
    await Deno.remove('./test-event-log', { recursive: true });
  });

  await t.step("should stream events in real-time", async () => {
    const log = new EventLogPersistence({
      path: './test-event-log',
      format: 'jsonl'
    });

    const receivedEvents: CausalOperation[] = [];
    
    // ストリーミングを開始
    const stream = log.stream();
    const reader = stream.getReader();
    
    // 非同期でイベントを読み取り
    const readPromise = (async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        receivedEvents.push(value);
      }
    })();

    // イベントを追加
    await log.append({
      id: "stream-1",
      type: "DDL",
      dependsOn: [],
      payload: { ddlType: "CREATE_TABLE", query: "CREATE NODE TABLE Stream1 (id STRING, PRIMARY KEY(id))" },
      clientId: "client-1",
      timestamp: Date.now()
    });

    await delay(50);

    await log.append({
      id: "stream-2",
      type: "DDL",
      dependsOn: ["stream-1"],
      payload: { ddlType: "CREATE_TABLE", query: "CREATE NODE TABLE Stream2 (id STRING, PRIMARY KEY(id))" },
      clientId: "client-2",
      timestamp: Date.now()
    });

    await delay(50);

    // ストリームを終了
    await reader.cancel();
    await readPromise;

    // リアルタイムで受信したイベントを確認
    assertEquals(receivedEvents.length, 2, "Should receive 2 events via stream");
    assertEquals(receivedEvents[0].id, "stream-1");
    assertEquals(receivedEvents[1].id, "stream-2");

    // クリーンアップ
    await log.close();
    await Deno.remove('./test-event-log', { recursive: true });
  });
});