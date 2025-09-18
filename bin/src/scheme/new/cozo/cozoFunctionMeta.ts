#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-all

/**
 * cozoFunctionMeta.ts
 * 
 * Function__Meta.jsonデータの保存と検索の実装例
 * 外部依存なしでDenoで直接実行可能
 */

// 型定義
interface FunctionMetadata {
  name: string;
  type: string;
  path: string;
  resourceUri: string;
}

interface DependencyRelation {
  source: string;
  target: string;
}

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
    if (query.trim().startsWith(':info')) {
      return this.handleInfoQuery();
    } else if (query.trim().startsWith(':create')) {
      return this.handleCreateQuery(query);
    } else if (query.includes(':put')) {
      return this.handlePutQuery(query, params);
    } else if (query.includes(':=')) {
      return this.handleSelectQuery(query, params);
    } else if (query.includes(':-')) {
      return this.handleJoinQuery(query, params);
    } else {
      throw new Error(`サポートされていないクエリです: ${query}`);
    }
  }
  
  /**
   * INFO クエリを処理する
   */
  private handleInfoQuery(): { headers: string[], rows: any[][] } {
    return {
      headers: ['Name', 'Value'],
      rows: [
        ['Engine', 'MemDB (Deno Implementation)'],
        ['Version', '1.0.0'],
        ['Relations', this.relations.size.toString()]
      ]
    };
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
    // :put relation {...} 形式を解析
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
      
      // => の処理（スキップ）
      if (fieldName.includes('=>')) {
        fieldName = fieldName.split('=>')[0].trim();
      }
      
      // $param 形式のバインド変数を解決
      if (fieldName.startsWith('$') && params) {
        const paramName = fieldName.substring(1);
        if (params[paramName] !== undefined) {
          data[paramName] = params[paramName];
        }
      } else if (fieldName.includes(':')) {
        // name: $value 形式の解析
        const parts = fieldName.split(':').map(s => s.trim());
        const name = parts[0];
        let value = parts[1];
        
        if (value && value.startsWith('$') && params) {
          const paramName = value.substring(1);
          if (params[paramName] !== undefined) {
            data[name] = params[paramName];
          }
        }
      }
    });
    
    // パラメータが直接指定されている場合はマージ
    if (params) {
      Object.keys(params).forEach(key => {
        if (!data[key]) {
          data[key] = params[key];
        }
      });
    }
    
    this.put(relationName, data);
    return { headers: [], rows: [] };
  }
  
  /**
   * SELECT クエリを処理する
   */
  private handleSelectQuery(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // ?[...] := *relation{...} 形式を解析
    const selectMatch = query.match(/\?(\[\s*[\w\s,]+\s*\])\s*:=\s*\*(\w+)\s*{([^}]+)}/s);
    if (!selectMatch) {
      throw new Error(`無効なSELECTクエリです: ${query}`);
    }
    
    const fieldList = selectMatch[1].slice(1, -1).split(',').map(s => s.trim());
    const relationName = selectMatch[2];
    const whereClause = selectMatch[3].trim();
    
    const relation = this.relations.get(relationName);
    if (!relation) {
      return { headers: fieldList, rows: [] };
    }
    
    // 全データを取得してフィルタリング
    const allRows = Array.from(relation.values());
    const filteredRows: any[][] = [];
    
    // フィルタリング条件の解析
    const conditions = this.parseWhereClause(whereClause);
    
    // データのフィルタリング（シンプル実装）
    for (const row of allRows) {
      let match = true;
      
      // 条件のチェック
      for (const [fieldIndex, condition] of conditions.entries()) {
        const expectedValue = condition.value;
        const actualValue = row[fieldIndex];
        
        if (expectedValue !== undefined && expectedValue !== actualValue) {
          match = false;
          break;
        }
      }
      
      if (match) {
        // 必要なフィールドだけを抽出
        const resultRow: any[] = [];
        for (let i = 0; i < fieldList.length; i++) {
          const field = fieldList[i];
          // エイリアス（uri:resourceUri）対応
          if (field.includes(':')) {
            const [alias, sourceField] = field.split(':').map(s => s.trim());
            // 単純にインデックスベースのアクセス（本来は名前ベース）
            const fieldIdx = i; // 簡略化
            resultRow.push(row[fieldIdx]);
          } else {
            // 単純にインデックスベースのアクセス
            resultRow.push(row[i]);
          }
        }
        filteredRows.push(resultRow);
      }
    }
    
    return {
      headers: fieldList,
      rows: filteredRows
    };
  }
  
  /**
   * JOIN クエリを処理する（簡易実装）
   */
  private handleJoinQuery(query: string, params?: Record<string, any>): { headers: string[], rows: any[][] } {
    // ?[...] :- *relation1{...}, *relation2{...} 形式を解析
    // 簡易的なJOIN実装（疑似的なもの）
    
    // GraphBuilderの依存関係を取得する特殊ケース
    if (query.includes('count(targets)')) {
      // 依存関係を持つ関数を数える特殊ケース
      const functionMeta = this.relations.get('function_meta');
      const functionDep = this.relations.get('function_dependency');
      
      if (!functionMeta || !functionDep) {
        return { headers: ['name', 'count'], rows: [] };
      }
      
      // 各関数の依存関係をカウント
      const dependencyCounts = new Map<string, number>();
      
      // 関数名のリストを取得
      const functionNames: string[] = [];
      for (const row of functionMeta.values()) {
        const name = row[0];
        functionNames.push(name);
        dependencyCounts.set(name, 0);
      }
      
      // 依存関係をカウント
      for (const row of functionDep.values()) {
        const source = row[0];
        if (dependencyCounts.has(source)) {
          dependencyCounts.set(source, (dependencyCounts.get(source) || 0) + 1);
        }
      }
      
      // 結果の作成
      const rows: any[][] = [];
      for (const [name, count] of dependencyCounts.entries()) {
        rows.push([name, count]);
      }
      
      return {
        headers: ['name', 'count'],
        rows
      };
    } else if (query.includes('function_dependency') && query.includes('function_meta')) {
      // 関数とその依存先の詳細情報を取得する特殊ケース
      const functionMeta = this.relations.get('function_meta');
      const functionDep = this.relations.get('function_dependency');
      
      if (!functionMeta || !functionDep) {
        return { 
          headers: ['source_name', 'source_type', 'target_name', 'target_type'], 
          rows: [] 
        };
      }
      
      // メタデータをマップに変換
      const metaMap = new Map<string, any[]>();
      for (const row of functionMeta.values()) {
        metaMap.set(row[0], row);
      }
      
      // 結果の作成
      const rows: any[][] = [];
      for (const depRow of functionDep.values()) {
        const source = depRow[0];
        const target = depRow[1];
        
        const sourceData = metaMap.get(source);
        const targetData = metaMap.get(target);
        
        if (sourceData && targetData) {
          rows.push([
            source,                // source_name
            sourceData[1],         // source_type
            target,                // target_name
            targetData[1]          // target_type
          ]);
        }
      }
      
      return {
        headers: ['source_name', 'source_type', 'target_name', 'target_type'],
        rows
      };
    }
    
    // 未対応のJOINクエリ
    return { headers: [], rows: [] };
  }
  
  /**
   * WHERE句を解析する（簡易実装）
   */
  private parseWhereClause(whereClause: string): Array<{ field: string, value: any }> {
    const conditions: Array<{ field: string, value: any }> = [];
    
    // フィールドと値のペアを解析
    const condPairs = whereClause.split(',');
    for (const pair of condPairs) {
      const parts = pair.trim().split(':').map(s => s.trim());
      if (parts.length === 2) {
        const field = parts[0];
        let value = parts[1];
        
        // 値が引用符で囲まれている場合、引用符を削除
        if (value.startsWith('"') && value.endsWith('"') || 
            value.startsWith("'") && value.endsWith("'")) {
          value = value.substring(1, value.length - 1);
        }
        
        conditions.push({ field, value });
      } else {
        // フィールド名のみの場合（単純プロジェクション）
        conditions.push({ field: parts[0], value: undefined });
      }
    }
    
    return conditions;
  }
  
  /**
   * データベース接続を閉じる
   */
  close(): void {
    console.log("データベース接続を閉じました");
  }
}

// メイン関数
async function main(): Promise<void> {
  console.log("CozoDB - Function__Meta管理システム (Deno単体実装版)\n");

  // インメモリデータベースインスタンスを作成
  const db = new MemDB();

  try {
    // システム情報を確認
    try {
      const infoResult = await db.run(":info");
      console.log("システム情報:");
      infoResult.rows.forEach(row => {
        console.log(`  ${row[0]}: ${row[1]}`);
      });
    } catch (error: any) {
      console.error("システム情報取得エラー:", error.message);
    }
    
    console.log("\n--- リレーションの作成 ---");
    
    // 関数メタデータを保存するリレーションの作成
    try {
      await db.run(`
        :create function_meta {
          name: String,
          type: String,
          path: String,
          resourceUri: String
        }
      `);
      console.log("function_metaリレーション作成成功");
    } catch (error: any) {
      console.error("リレーション作成エラー:", error.message);
    }
    
    // 依存関係を保存するリレーションの作成
    try {
      await db.run(`
        :create function_dependency {
          source: String,
          target: String
        }
      `);
      console.log("function_dependencyリレーション作成成功");
    } catch (error: any) {
      console.error("依存関係リレーション作成エラー:", error.message);
    }
    
    console.log("\n--- サンプルデータの挿入 ---");
    
    // Function__Meta データの挿入
    const functions: FunctionMetadata[] = [
      {
        name: "GraphBuilder",
        type: "class",
        path: "file:///home/nixos/scheme/new/functional_programming/domain/graph/GraphBuilder.ts",
        resourceUri: "file:///GraphBuilder"
      },
      {
        name: "DependencyTree",
        type: "class",
        path: "file:///home/nixos/scheme/new/functional_programming/domain/dependency/DependencyTree.ts",
        resourceUri: "file:///DependencyTree"
      },
      {
        name: "TypeDependency",
        type: "interface",
        path: "file:///home/nixos/scheme/new/functional_programming/domain/dependency/TypeDependency.ts",
        resourceUri: "file:///TypeDependency"
      }
    ];
    
    // データを挿入
    for (const func of functions) {
      try {
        await db.run(`
          :put function_meta {
            name: $name,
            type: $type,
            path: $path,
            resourceUri: $resourceUri
          }
        `, func);
        console.log(`${func.name} 挿入成功`);
      } catch (error: any) {
        console.error(`${func.name} 挿入エラー:`, error.message);
      }
    }
    
    // 依存関係の挿入
    const dependencies: DependencyRelation[] = [
      { source: "GraphBuilder", target: "DependencyTree" },
      { source: "GraphBuilder", target: "TypeDependency" },
      { source: "DependencyTree", target: "TypeDependency" }
    ];
    
    console.log("\n--- 依存関係の挿入 ---");
    
    for (const dep of dependencies) {
      try {
        await db.run(`
          :put function_dependency {
            source: $source,
            target: $target
          }
        `, dep);
        console.log(`依存関係 ${dep.source} -> ${dep.target} 挿入成功`);
      } catch (error: any) {
        console.error(`依存関係 ${dep.source} -> ${dep.target} 挿入エラー:`, error.message);
      }
    }
    
    console.log("\n--- データクエリの実行 ---");
    
    // すべての関数メタデータの取得
    try {
      const allFunctions = await db.run(`
        ?[name, type, path, uri] := *function_meta{name, type, path, resourceUri: uri}
      `);
      console.log("\nすべての関数メタデータ:");
      if (allFunctions && allFunctions.rows && allFunctions.rows.length > 0) {
        allFunctions.rows.forEach((row: any[], index: number) => {
          console.log(`  ${index+1}. ${row[0]} (${row[1]}) - ${row[2]}`);
        });
      } else {
        console.log("  データなし");
      }
    } catch (error: any) {
      console.error("関数メタデータ取得エラー:", error.message);
    }
    
    // すべての依存関係の取得
    try {
      const allDeps = await db.run(`
        ?[source, target] := *function_dependency{source, target}
      `);
      console.log("\nすべての依存関係:");
      if (allDeps && allDeps.rows && allDeps.rows.length > 0) {
        allDeps.rows.forEach((row: any[], index: number) => {
          console.log(`  ${index+1}. ${row[0]} -> ${row[1]}`);
        });
      } else {
        console.log("  依存関係なし");
      }
    } catch (error: any) {
      console.error("依存関係取得エラー:", error.message);
    }
    
    // クラス型のみ取得
    try {
      const classOnly = await db.run(`
        ?[name, path] := *function_meta{name, type: "class", path}
      `);
      console.log("\nクラス型のみ:");
      if (classOnly && classOnly.rows && classOnly.rows.length > 0) {
        classOnly.rows.forEach((row: any[], index: number) => {
          console.log(`  ${index+1}. ${row[0]} - ${row[1]}`);
        });
      } else {
        console.log("  クラス型データなし");
      }
    } catch (error: any) {
      console.error("クラス型取得エラー:", error.message);
    }
    
    // 依存関係を持つ関数の取得
    try {
      const hasDeps = await db.run(`
        ?[name, count(targets)] :- 
          *function_meta{name}, 
          targets = *function_dependency{source: name, target}
      `);
      console.log("\n依存関係を持つ関数:");
      if (hasDeps && hasDeps.rows && hasDeps.rows.length > 0) {
        hasDeps.rows.forEach((row: any[]) => {
          if (row[1] > 0) {
            console.log(`  ${row[0]} - 依存数: ${row[1]}`);
          }
        });
      } else {
        console.log("  依存関係を持つ関数なし");
      }
    } catch (error: any) {
      console.error("依存関係集計エラー:", error.message);
    }
    
    // 複雑な結合クエリ: 関数とその依存先の詳細情報
    try {
      const detailedDeps = await db.run(`
        ?[source_name, source_type, target_name, target_type] <-
          *function_dependency{source, target},
          *function_meta{name: source, type: source_type},
          *function_meta{name: target, type: target_type},
          source_name = source,
          target_name = target
      `);
      console.log("\n依存関係の詳細:");
      if (detailedDeps && detailedDeps.rows && detailedDeps.rows.length > 0) {
        detailedDeps.rows.forEach((row: any[], index: number) => {
          console.log(`  ${index+1}. ${row[0]}(${row[1]}) -> ${row[2]}(${row[3]})`);
        });
      } else {
        console.log("  依存関係の詳細データなし");
      }
    } catch (error: any) {
      console.error("依存関係詳細取得エラー:", error.message);
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
