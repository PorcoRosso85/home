#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-all

/**
 * CozoDBの最小限の機能を使用した実装例（純粋なTypeScript実装）
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
    const matches = query.match(/:create\s+(\w+)\s*{([^}]+)}/);
    if (!matches) {
      throw new Error(`無効なCREATEクエリです: ${query}`);
    }
    
    const relationName = matches[1];
    const schemaText = matches[2];
    
    // スキーマ定義を解析
    const schema: Record<string, string> = {};
    schemaText.split(',').forEach(field => {
      const [name, type] = field.trim().split(':').map(s => s.trim());
      if (name && type) {
        schema[name] = type;
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
    const relationMatch = query.match(/:put\s+(\w+)\s*{([^}]+)}/);
    if (!relationMatch) {
      throw new Error(`無効なPUTクエリです: ${query}`);
    }
    
    const relationName = relationMatch[1];
    const data: Record<string, any> = {};
    
    // フィールド定義を解析
    const fieldsText = relationMatch[2];
    fieldsText.split(',').forEach(field => {
      let fieldName = field.trim();
      
      // => の処理（現在はスキップ）
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
        // 実際のクエリ解析ではもっと複雑ですが、シンプル化
        data[fieldName] = fieldName;
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
    const selectMatch = query.match(/\?(\[[\w\s,]+\])\s*:=\s*\*(\w+)\s*\[([\w\s,]+)\]/);
    if (!selectMatch) {
      throw new Error(`無効なSELECTクエリです: ${query}`);
    }
    
    const fieldList = selectMatch[1].slice(1, -1).split(',').map(s => s.trim());
    const relationName = selectMatch[2];
    const relationFields = selectMatch[3].split(',').map(s => s.trim());
    
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
   * データベース接続を閉じる
   */
  close(): void {
    // インメモリDBなので特に何もしない
    console.log("データベース接続を閉じました");
  }
}

// メイン関数
async function main(): Promise<void> {
  console.log("CozoDB 最小機能デモ開始 (純粋なTypeScript実装)");

  // インメモリデータベースインスタンスを作成
  const db = new MemDB();

  try {
    // 簡易的なリレーション作成
    try {
      await db.run(`:create simple_relation {
        name: String,
        value: Int
      }`);
    } catch (error: any) {
      console.error("リレーション作成エラー:", error.message);
    }

    // データ挿入
    const data = [
      { name: "項目1", value: 100 },
      { name: "項目2", value: 200 },
      { name: "項目3", value: 300 }
    ];

    for (const item of data) {
      try {
        await db.run(`?[name, value] <- [[$name, $value]] :put simple_relation {name, value => }`, item);
        console.log(`${item.name} 挿入成功`);
      } catch (error: any) {
        console.error(`${item.name} 挿入エラー:`, error.message);
      }
    }

    // データ取得
    try {
      const result = await db.run("?[n, v] := *simple_relation[n, v]");

      console.log("\n取得したデータ:");
      if (result && result.rows) {
        result.rows.forEach((row, index) => {
          console.log(`  ${index + 1}. ${row[0]}: ${row[1]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("データ取得エラー:", error.message);
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
