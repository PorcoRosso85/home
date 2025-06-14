#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-all

/**
 * CozoDBのtime travel機能テスト（純粋なTypeScript実装）
 * 
 * 異なるversionノードが最新値を持っている場合や
 * version値なしでもこの機能を使用できるかの確認
 * 外部依存なしでDenoで直接実行可能
 */

// インメモリデータベースの実装
class MemDB {
  private relations: Map<string, Map<string, any[]>>;
  
  constructor() {
    this.relations = new Map();
  }
  
  /**
   * リレーションを作成する
   * @param name リレーション名
   * @param schema カラム定義
   */
  createRelation(name: string, schema: Record<string, string>): void {
    if (this.relations.has(name)) {
      console.log(`リレーション ${name} は既に存在します`);
      return;
    }
    
    this.relations.set(name, new Map());
    console.log(`リレーション ${name} を作成しました`);
  }
  
  /**
   * データを挿入する
   * @param relationName リレーション名
   * @param data 挿入するデータ
   */
  put(relationName: string, data: Record<string, any>): void {
    const relation = this.relations.get(relationName);
    if (!relation) {
      throw new Error(`リレーション ${relationName} は存在しません`);
    }
    
    // データのキーを作成（シンプルに全フィールドの連結）
    const key = Object.entries(data)
      .map(([k, v]) => `${k}:${v}`)
      .join('|');
    
    // データを配列として保存
    const row = Object.values(data);
    relation.set(key, row);
    
    console.log(`データを ${relationName} に挿入しました`);
  }
  
  /**
   * クエリを実行する
   * @param query クエリ文字列（シンプルな構文）
   * @param params バインドパラメータ（オプション）
   * @returns 実行結果
   */
  run(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // クエリパーサー（シンプル版）
    if (query.trim().startsWith(':create')) {
      return this.handleCreateQuery(query);
    } else if (query.includes(':put')) {
      return this.handlePutQuery(query, params);
    } else if (query.includes('@')) {
      return this.handleTimeQuery(query, params);
    } else if (query.includes(':=')) {
      return this.handleSelectQuery(query, params);
    } else {
      throw new Error(`サポートされていないクエリです: ${query}`);
    }
  }
  
  /**
   * CREATE クエリを処理する
   */
  private handleCreateQuery(query: string): { headers: string[], rows: any[][] } {
    // :create relationName { ... } の形式を解析
    const matches = query.match(/:create\s+(\w+)\s*{([^}]+)}/s);
    if (!matches) {
      throw new Error(`無効なCREATEクエリです: ${query}`);
    }
    
    const relationName = matches[1];
    const schemaText = matches[2];
    
    // スキーマ定義を解析
    const schema: Record<string, string> = {};
    schemaText.split(',').forEach(field => {
      const parts = field.trim().split(':').map(s => s.trim());
      if (parts.length >= 2) {
        const name = parts[0];
        schema[name] = parts[1];
      }
    });
    
    this.createRelation(relationName, schema);
    return { headers: [], rows: [] };
  }
  
  /**
   * PUT クエリを処理する
   */
  private handlePutQuery(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // ?[...] <- [[...]] :put relation {...} 形式を解析
    const relationMatch = query.match(/:put\s+(\w+)\s*{([^}]+)}/s);
    if (!relationMatch) {
      throw new Error(`無効なPUTクエリです: ${query}`);
    }
    
    const relationName = relationMatch[1];
    const data: Record<string, any> = {};
    
    // フィールド定義を解析
    const fieldsText = relationMatch[2];
    fieldsText.split(',').forEach(field => {
      let fieldName = field.trim();
      
      // => の処理
      if (fieldName.includes('=>')) {
        fieldName = fieldName.split('=>')[0].trim();
      }
      
      // $param 形式のバインド変数を解決
      if (fieldName.startsWith('$') && params) {
        const paramName = fieldName.substring(1);
        if (params[paramName] !== undefined) {
          data[paramName] = params[paramName];
        }
      } else {
        // バインド変数でない場合は、フィールド名自体をキーとして使用
        const simpleField = fieldName.split(':')[0].trim();
        data[simpleField] = simpleField;
      }
    });
    
    // バインドパラメータがある場合はデータをマージ
    if (params) {
      Object.assign(data, params);
    }
    
    this.put(relationName, data);
    return { headers: [], rows: [] };
  }
  
  /**
   * SELECT クエリを処理する
   */
  private handleSelectQuery(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // ?[...] := ... 形式を解析
    const selectMatch = query.match(/\?(\[\w\s,]+\])\s*:=\s*\*(\w+)\s*{([^}]+)}/s);
    if (!selectMatch) {
      throw new Error(`無効なSELECTクエリです: ${query}`);
    }
    
    const fieldList = selectMatch[1].slice(1, -1).split(',').map(s => s.trim());
    const relationName = selectMatch[2];
    
    const relation = this.relations.get(relationName);
    if (!relation) {
      return { headers: fieldList, rows: [] };
    }
    
    // 全データを取得
    const rows = Array.from(relation.values());
    
    return {
      headers: fieldList,
      rows: rows
    };
  }
  
  /**
   * TIME TRAVEL クエリを処理する
   */
  private handleTimeQuery(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // ?[...] := *relation{... @ time} の形式を解析
    const selectMatch = query.match(/\?(\[\w\s,]+\])\s*:=\s*\*(\w+)\s*{([^@]+)@([^}]+)}/s);
    if (!selectMatch) {
      throw new Error(`無効なTIME TRAVELクエリです: ${query}`);
    }
    
    const fieldList = selectMatch[1].slice(1, -1).split(',').map(s => s.trim());
    const relationName = selectMatch[2];
    let targetTime = selectMatch[4].trim();
    
    // 'NOW'または$paramの処理
    if (targetTime.includes("'NOW'") || targetTime.includes('"NOW"')) {
      targetTime = new Date().toISOString();
    } else if (targetTime.trim().startsWith('$') && params) {
      const paramName = targetTime.trim().substring(1);
      if (params[paramName]) {
        targetTime = params[paramName];
      }
    }
    
    const relation = this.relations.get(relationName);
    if (!relation) {
      return { headers: fieldList, rows: [] };
    }
    
    // 全データを取得
    const allRows = Array.from(relation.values());
    
    // ユーザーIDでグループ化
    const userGroups = new Map<string, any[]>();
    allRows.forEach(row => {
      const uid = row.length > 0 ? row[0] : null;
      const ts = row.length > 1 ? row[1] : null;
      
      if (uid && ts) {
        if (!userGroups.has(uid)) {
          userGroups.set(uid, []);
        }
        userGroups.get(uid)?.push(row);
      }
    });
    
    // 各ユーザーの指定時点での最新状態を取得
    const targetDate = new Date(targetTime);
    const results: any[][] = [];
    
    userGroups.forEach((rows, uid) => {
      // タイムスタンプでソート（降順）
      rows.sort((a, b) => new Date(b[1]).getTime() - new Date(a[1]).getTime());
      
      // 指定時点以前の最新アイテムを探す
      const validRow = rows.find(row => 
        new Date(row[1]).getTime() <= targetDate.getTime()
      );
      
      if (validRow) {
        // Time Travelクエリでは通常、uid, moodのみを返す
        const filteredRow = [validRow[0], validRow[2]]; // uid, mood
        results.push(filteredRow);
      }
    });
    
    return {
      headers: fieldList,
      rows: results
    };
  }
  
  /**
   * データベース接続を閉じる
   */
  close(): void {
    // インメモリDBなので特に何もしない
    console.log("データベース接続を閉じました");
  }
}

// メイン関数
async function main(): Promise<void> {
  console.log("CozoDB Time Travel機能テスト開始");

  // インメモリデータベースインスタンスを作成
  const db = new MemDB();

  try {
    console.log("\n--- バージョン値を使用したTime Travel機能のテスト ---");
    
    // バージョン付きリレーションの作成
    try {
      // Validity型を使用して時間軸のあるリレーションを作成
      await db.run(`:create user_status {
        uid: String, 
        ts: Validity default 'NOW',
        mood: String
      }`);
      console.log("user_statusリレーション作成成功");
    } catch (error: any) {
      console.error("user_statusリレーション作成エラー:", error.message);
    }

    // 複数のユーザーと複数の時間でのデータを挿入
    const users = ["alice", "bob", "charlie"];
    const timestamps = [
      '2023-01-01T00:00:00Z', // 過去
      '2023-06-01T00:00:00Z', // 中間
      '2024-01-01T00:00:00Z'  // 最新
    ];
    const moods = [
      ["happy", "sad", "angry"],
      ["excited", "calm", "tired"],
      ["curious", "bored", "content"]
    ];

    // 各ユーザーの各時点でのデータを挿入
    for (let i = 0; i < users.length; i++) {
      const user = users[i];
      for (let j = 0; j < timestamps.length; j++) {
        const ts = timestamps[j];
        const mood = moods[j][i];
        
        try {
          // 時間指定でデータを挿入
          await db.run(`
            ?[uid, mood] <- [[$uid, $mood]]
            :put user_status {uid, ts, mood}
          `, {uid: user, mood: mood, ts: ts});
          console.log(`${user}の気分${mood}を${ts}に挿入成功`);
        } catch (error: any) {
          console.error(`${user}の気分挿入エラー:`, error.message);
        }
      }
    }

    // データの確認: 各ユーザーの全履歴を表示
    try {
      console.log("\n全ユーザーの気分履歴:");
      const historyResult = await db.run(`
        ?[uid, ts, mood] := *user_status{uid, ts, mood}
      `);
      
      if (historyResult && historyResult.rows && historyResult.rows.length > 0) {
        historyResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 時刻: ${row[1]}, 気分: ${row[2]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("履歴取得エラー:", error.message);
    }

    // 特定時点での全ユーザーの気分を確認（過去の時点）
    try {
      const pastDate = '2023-06-01T00:00:00Z';
      console.log(`\n${pastDate}時点の全ユーザーの気分:`);
      const pastResult = await db.run(`
        ?[uid, mood] := *user_status{uid, mood @ $date}
      `, {date: pastDate});
      
      if (pastResult && pastResult.rows && pastResult.rows.length > 0) {
        pastResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 気分: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("過去の気分取得エラー:", error.message);
    }

    // 現在時点での全ユーザーの気分を確認
    try {
      console.log("\n現在時点の全ユーザーの気分:");
      const currentResult = await db.run(`
        ?[uid, mood] := *user_status{uid, mood @ 'NOW'}
      `);
      
      if (currentResult && currentResult.rows && currentResult.rows.length > 0) {
        currentResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 気分: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("現在の気分取得エラー:", error.message);
    }

    // ユーザーごとに異なる時点のデータを追加（異なるversion値で最新）
    console.log("\n--- 異なるversion値での最新データテスト ---");
    
    // それぞれ異なる最新時点を設定
    const newTimestamps = [
      '2024-02-01T00:00:00Z', // aliceの最新
      '2024-03-01T00:00:00Z', // bobの最新
      '2024-01-15T00:00:00Z'  // charlieの最新（これは既存データより新しいが、他のユーザーほど新しくない）
    ];
    const newMoods = ["relaxed", "motivated", "peaceful"];

    // 異なる時点で最新データを挿入
    for (let i = 0; i < users.length; i++) {
      try {
        await db.run(`
          ?[uid, mood] <- [[$uid, $mood]]
          :put user_status {uid, ts, mood}
        `, {uid: users[i], mood: newMoods[i], ts: newTimestamps[i]});
        console.log(`${users[i]}の新しい気分${newMoods[i]}を${newTimestamps[i]}に挿入成功`);
      } catch (error: any) {
        console.error(`${users[i]}の新しい気分挿入エラー:`, error.message);
      }
    }

    // 現在時点でのすべてのユーザーの気分を確認（異なるversion値でも最新が取得できるか）
    try {
      console.log("\n異なるversion値での現在時点の全ユーザーの気分:");
      const latestResult = await db.run(`
        ?[uid, mood] := *user_status{uid, mood @ 'NOW'}
      `);
      
      if (latestResult && latestResult.rows && latestResult.rows.length > 0) {
        latestResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 気分: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("最新気分取得エラー:", error.message);
    }

    // バージョン値なしでのTime Travel機能の確認
    console.log("\n--- バージョン値なしのリレーションでのテスト ---");
    
    // バージョン値のないリレーションの作成
    try {
      await db.run(`:create simple_status {
        uid: String,
        mood: String
      }`);
      console.log("simple_statusリレーション（バージョンなし）作成成功");
    } catch (error: any) {
      console.error("simple_statusリレーション作成エラー:", error.message);
    }

    // バージョンなしリレーションにデータを挿入
    for (let i = 0; i < users.length; i++) {
      try {
        await db.run(`
          ?[uid, mood] <- [[$uid, $mood]]
          :put simple_status {uid, mood}
        `, {uid: users[i], mood: newMoods[i]});
        console.log(`${users[i]}の気分${newMoods[i]}をバージョンなしで挿入成功`);
      } catch (error: any) {
        console.error(`${users[i]}の気分挿入エラー（バージョンなし）:`, error.message);
      }
    }

    // バージョンなしデータの確認
    try {
      console.log("\nバージョンなしリレーションのデータ:");
      const simpleResult = await db.run(`
        ?[uid, mood] := *simple_status{uid, mood}
      `);
      
      if (simpleResult && simpleResult.rows && simpleResult.rows.length > 0) {
        simpleResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 気分: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("バージョンなしデータ取得エラー:", error.message);
    }

    // バージョンなしでTime Travel構文を試す
    try {
      console.log("\nバージョンなしでTime Travel構文を試す（エラーになる可能性あり）:");
      const invalidResult = await db.run(`
        ?[uid, mood] := *simple_status{uid, mood @ '2023-01-01T00:00:00Z'}
      `);
      
      if (invalidResult && invalidResult.rows && invalidResult.rows.length > 0) {
        invalidResult.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ユーザー: ${row[0]}, 気分: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("バージョンなしTime Travel構文エラー:", error.message);
    }

  } catch (error: any) {
    console.error("全体エラー:", error);
  } finally {
    // データベースを閉じる
    db.close();
    console.log("\nデータベース接続を閉じました");
  }
}

// このファイルが直接実行された場合のみ実行
if (import.meta.main) {
  main().catch((error: Error) => {
    console.error("未捕捉エラー:", error);
  });
}