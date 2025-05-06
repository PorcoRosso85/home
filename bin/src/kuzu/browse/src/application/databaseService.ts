/**
 * アプリケーション層のデータベースサービス
 * 
 * データベース接続と基本操作を管理するシンプルなサービス
 */

import { 
  initializeDatabase, 
  isError,
  cleanupDatabaseResources
} from '../infrastructure/database/databaseService';

/**
 * データベース操作の結果型
 */
export interface DatabaseOperationResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * データベース接続状態
 */
interface ConnectionState {
  isConnected: boolean;
  lastTestedAt: number;
  errorCount: number;
  dbPath: string;
}

/**
 * データベースサービスクラス
 * 
 * データベース接続と状態管理を行う
 */
export class DatabaseService {
  private conn: any = null;
  private db: any = null;
  private kuzu: any = null;
  private connectionState: ConnectionState = {
    isConnected: false,
    lastTestedAt: 0,
    errorCount: 0,
    dbPath: ''
  };
  
  /**
   * Parquetデータをインポートする
   * 
   * @returns インポート結果
   */
  public async importParquetData(): Promise<DatabaseOperationResult> {
    try {
      if (!this.conn || !this.connectionState.isConnected) {
        return {
          success: false,
          error: 'データベースに接続されていないため、データをインポートできません'
        };
      }
      
      console.log('サンプルデータの初期化を開始します...');
      
      try {
        // 最小限のサンプルノードを作成
        const createNodeQuery = `
        CREATE (n:Node {id: "node-1", name: "テストノード1"})
        CREATE (m:Node {id: "node-2", name: "テストノード2"})
        CREATE (n)-[:CONNECTS_TO {weight: 1.0}]->(m)
        `;
        
        // クエリを実行
        console.log('サンプルノード作成クエリを実行中...');
        try {
          await this.executeDirectQuery(createNodeQuery);
          console.log('サンプルノード作成成功');
        } catch (createErr) {
          console.warn('ノード作成エラー:', createErr.message);
          return {
            success: false,
            error: `ノード作成エラー: ${createErr.message}`
          };
        }
      } catch (err) {
        console.error('データの初期化中にエラーが発生:', err);
        return {
          success: false,
          error: `データの初期化中にエラーが発生しました: ${err.message}`
        };
      }
      
      // データベース統計の取得
      try {
        const statsQuery = `MATCH (n) RETURN count(n) AS nodeCount`;
        const statsResult = await this.executeDirectQuery(statsQuery);
        const nodeCount = (statsResult.success && statsResult.data && statsResult.data.length > 0) ?
          statsResult.data[0].nodeCount || 0 : 0;
        
        const edgeQuery = `MATCH ()-[r]->() RETURN count(r) AS edgeCount`;
        const edgeResult = await this.executeDirectQuery(edgeQuery);
        const edgeCount = (edgeResult.success && edgeResult.data && edgeResult.data.length > 0) ?
          edgeResult.data[0].edgeCount || 0 : 0;
        
        return {
          success: true,
          data: {
            message: 'サンプルデータの初期化が完了しました',
            nodeCount,
            edgeCount
          }
        };
      } catch (statsErr) {
        console.warn('統計取得エラー:', statsErr);
        return {
          success: true,
          data: {
            message: 'サンプルデータの初期化が完了しました（統計取得失敗）',
            nodeCount: 0,
            edgeCount: 0
          }
        };
      }
    } catch (error) {
      console.error('データ初期化エラー:', error);
      return {
        success: false,
        error: `データの初期化に失敗しました: ${error.message}`
      };
    }
  }

  /**
   * データベースに接続する
   * 
   * @param importParquet Parquetデータをインポートするかどうか
   * @returns 接続結果
   */
  public async connect(importParquet: boolean = true): Promise<DatabaseOperationResult> {
    try {
      // すでに接続されている場合は接続テストで確認
      if (this.conn) {
        console.log('既存の接続があります。接続テストを実行...');
        
        try {
          // 現在時刻と最後のテスト時刻の差を確認
          const now = Date.now();
          const timeSinceLastTest = now - this.connectionState.lastTestedAt;
          
          // 10秒以内に接続テスト済みなら再テストはスキップ
          if (this.connectionState.isConnected && timeSinceLastTest < 10000) {
            console.log('最近テスト済みの接続です。再利用します。', 
              `最終テスト: ${Math.round(timeSinceLastTest / 1000)}秒前`);
            return {
              success: true,
              data: { 
                message: 'データベースに既に接続されています'
              }
            };
          }
          
          // 軽量なテストクエリを実行
          const testQuery = 'RETURN 1 AS test';
          console.log('既存接続テストクエリ実行:', testQuery);
          const testResult = await this.conn.query(testQuery);
          const testObj = await testResult.getAllObjects();
          
          if (testResult && testObj && testObj.length > 0) {
            console.log('既存接続テスト成功:', testObj);
            
            // 接続状態を更新
            this.connectionState = {
              ...this.connectionState,
              isConnected: true,
              lastTestedAt: now,
              errorCount: 0
            };
            
            return {
              success: true,
              data: { 
                message: 'データベースに既に接続されています'
              }
            };
          } else {
            console.warn('既存接続テスト失敗: 有効な結果がありません');
            this.connectionState.errorCount++;
          }
        } catch (testErr) {
          console.warn('既存接続テストエラー:', testErr);
          this.connectionState.errorCount++;
          
          // 接続が機能していない場合は再接続を試みる
          console.log('既存の接続に問題があるため、再接続を試みます');
          
          try {
            // 既存リソースのクリーンアップを試みる
            await cleanupDatabaseResources(this.conn, this.db).catch(e => 
              console.warn('既存リソースクリーンアップエラー:', e));
          } catch (cleanupErr) {
            console.warn('クリーンアップエラー:', cleanupErr);
          }
          
          // 再接続のためリセット
          this.conn = null;
          this.db = null;
          this.kuzu = null;
          
          // グローバル変数もクリア
          window.conn = null;
          window.db = null;
          window.kuzu = null;
        }
      }
      
      // データベース初期化
      console.log('データベース接続を開始します...');
      const dbResult = await initializeDatabase();
      
      if (isError(dbResult)) {
        // 接続状態を更新
        this.connectionState = {
          ...this.connectionState,
          isConnected: false,
          lastTestedAt: Date.now(),
          errorCount: this.connectionState.errorCount + 1
        };
        
        return {
          success: false,
          error: dbResult.message
        };
      }
      
      const { kuzu, db, conn } = dbResult;
      
      // 接続が成功したかテスト
      try {
        console.log('新規接続のテスト実行中...');
        const testQuery = 'RETURN 1 AS test';
        const testResult = await conn.query(testQuery);
        const testObj = await testResult.getAllObjects();
        
        if (!testResult || !testObj || testObj.length === 0) {
          console.error('新規接続のテストに失敗: 有効な結果が返されませんでした');
          
          try {
            // 新しく作成したリソースのクリーンアップを試みる
            await cleanupDatabaseResources(conn, db).catch(e => 
              console.warn('新規リソースクリーンアップエラー:', e));
          } catch (cleanupErr) {
            console.warn('新規リソースクリーンアップエラー:', cleanupErr);
          }
          
          this.connectionState = {
            ...this.connectionState,
            isConnected: false,
            lastTestedAt: Date.now(),
            errorCount: this.connectionState.errorCount + 1
          };
          
          return {
            success: false,
            error: '接続は確立されましたが、テストクエリの実行に失敗しました'
          };
        }
        
        console.log('新規接続テスト成功:', testObj);
      } catch (testErr) {
        console.error('新規接続テストエラー:', testErr);
        
        try {
          // 新しく作成したリソースのクリーンアップを試みる
          await cleanupDatabaseResources(conn, db).catch(e => 
            console.warn('新規リソースクリーンアップエラー:', e));
        } catch (cleanupErr) {
          console.warn('新規リソースクリーンアップエラー:', cleanupErr);
        }
        
        this.connectionState = {
          ...this.connectionState,
          isConnected: false,
          lastTestedAt: Date.now(),
          errorCount: this.connectionState.errorCount + 1
        };
        
        return {
          success: false,
          error: `接続テストに失敗しました: ${testErr.message}`
        };
      }
      
      // すべてのテストに通過したら接続を保存
      this.kuzu = kuzu;
      this.db = db;
      this.conn = conn;
      
      // グローバル変数として保存（デバッグ用）
      window.kuzu = kuzu;
      window.db = db;
      window.conn = conn;
      
      // 接続パスを保存
      const dbPath = window.db_path || 'unknown';
      
      // 接続状態を更新
      this.connectionState = {
        isConnected: true,
        lastTestedAt: Date.now(),
        errorCount: 0,
        dbPath: dbPath
      };
      
      console.log('データベース接続が完了し、テスト済み:', this.connectionState);
      
      // Parquetデータをインポート（オプション）
      if (importParquet) {
        console.log('データベース接続成功後、Parquetデータのインポートを開始します...');
        try {
          const importResult = await this.importParquetData();
          if (!importResult.success) {
            console.warn('Parquetデータのインポートに失敗しました:', importResult.error);
            // インポートの失敗は接続自体の失敗とはみなさない
          } else {
            console.log('Parquetデータのインポートが完了しました:', importResult.data);
          }
        } catch (importErr) {
          console.warn('Parquetデータのインポート中にエラーが発生しました:', importErr);
          // インポートエラーは接続自体の成功には影響しない
        }
      }
      
      return {
        success: true,
        data: {
          message: 'データベースに接続しました',
          dbPath: dbPath
        }
      };
    } catch (error) {
      console.error('データベース接続エラー:', error);
      
      // 接続状態を更新
      this.connectionState = {
        ...this.connectionState,
        isConnected: false,
        lastTestedAt: Date.now(),
        errorCount: this.connectionState.errorCount + 1
      };
      
      return {
        success: false,
        error: `データベース接続に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * 直接Cypherクエリを実行する
   * 
   * @param query 実行するCypherクエリ
   * @returns クエリ実行結果
   */
  public async executeDirectQuery(query: string): Promise<DatabaseOperationResult> {
    try {
      // データベース接続確認
      if (!this.conn || !this.connectionState.isConnected) {
        console.log('クエリ実行前に接続が必要です');
        const connectResult = await this.connect();
        if (!connectResult.success) {
          return connectResult;
        }
      }
      
      // クエリ実行
      console.log(`クエリ実行: ${query}`);
      
      try {
        // Cypherクエリの種類を特定
        const queryType = this.identifyQueryType(query);
        console.log(`クエリタイプ: ${queryType}`);
        
        // 最大2回試行（最初のエラーが接続に関するものの場合）
        let attempt = 0;
        const maxAttempts = 2;
        
        while (attempt < maxAttempts) {
          try {
            // 実行メソッドはqueryタイプによって異なる
            let result;
            
            if (queryType === 'ddl' || queryType === 'create') {
              // CREATE系のクエリはexecuteメソッドを使用
              console.log('DDLクエリを実行します（executeメソッド使用）');
              result = await this.conn.execute(query);
            } else {
              // それ以外のクエリはqueryメソッドを使用
              console.log('DQLクエリを実行します（queryメソッド使用）');
              result = await this.conn.query(query);
            }
            
            // 結果の変換
            let resultData;
            if (result && result.getAllObjects) {
              resultData = await result.getAllObjects();
            } else {
              resultData = result || [{ message: 'クエリが成功しましたが、結果はありません' }];
            }
            
            // 接続状態を更新 (成功)
            this.connectionState.lastTestedAt = Date.now();
            this.connectionState.errorCount = 0;
            
            return {
              success: true,
              data: resultData
            };
          } catch (queryErr) {
            console.error(`クエリ実行エラー (試行 ${attempt + 1}/${maxAttempts}):`, queryErr);
            
            if (attempt + 1 < maxAttempts) {
              // 接続エラーの場合は再接続を試みる
              console.log('接続エラーの可能性があるため、再接続を試みます');
              try {
                // 再接続
                await this.disconnect();
                await this.connect(false);  // サンプルデータのインポートなし
                console.log('再接続成功。クエリを再試行します');
              } catch (reconnectErr) {
                console.error('再接続エラー:', reconnectErr);
                // 再接続に失敗した場合はエラーを返す
                return {
                  success: false,
                  error: `再接続に失敗しました: ${reconnectErr.message}`
                };
              }
            } else {
              // 最大試行回数に達した場合はエラーを返す
              return {
                success: false,
                error: `クエリ実行に失敗しました: ${queryErr.message}`
              };
            }
            
            attempt++;
          }
        }
        
        // ここに到達することはないはず（すでにreturnされているはず）
        return {
          success: false,
          error: '予期しないエラーが発生しました'
        };
      } catch (queryErr) {
        console.error('クエリ実行エラー:', queryErr);
        
        return {
          success: false,
          error: `クエリ実行に失敗しました: ${queryErr.message}`
        };
      }
    } catch (error) {
      console.error('クエリ実行処理エラー:', error);
      
      // 接続状態を更新 (エラー)
      this.connectionState.errorCount++;
      
      // エラーが続く場合は接続状態をリセット
      if (this.connectionState.errorCount > 3) {
        this.connectionState.isConnected = false;
      }
      
      return {
        success: false,
        error: `クエリ実行に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * Cypherクエリのタイプを識別する
   * 
   * @param query クエリ文字列
   * @returns クエリのタイプ ('ddl', 'create', 'match', 'other')
   */
  private identifyQueryType(query: string): string {
    const lowerQuery = query.toLowerCase().trim();
    
    if (lowerQuery.startsWith('create ')) {
      return 'create';
    } else if (lowerQuery.startsWith('drop ') || lowerQuery.startsWith('alter ')) {
      return 'ddl';
    } else if (lowerQuery.startsWith('match ')) {
      return 'match';
    } else if (lowerQuery.startsWith('return ')) {
      return 'return';
    } else {
      return 'other';
    }
  }
  
  /**
   * クエリにタイムアウトを設定して実行する
   * 
   * @param query 実行するクエリ文字列
   * @param timeoutMs タイムアウト時間（ミリ秒）
   * @returns クエリ結果またはタイムアウトエラー
   */
  private async executeQueryWithTimeout(query: string, timeoutMs: number = 5000): Promise<any> {
    return new Promise(async (resolve, reject) => {
      // タイムアウトタイマー
      const timer = setTimeout(() => {
        reject(new Error(`クエリがタイムアウト（${timeoutMs}ms）を超過しました: ${query}`));
      }, timeoutMs);
      
      try {
        // クエリ実行
        const result = await this.conn.query(query);
        // タイマーをクリア
        clearTimeout(timer);
        resolve(result);
      } catch (error) {
        // タイマーをクリア
        clearTimeout(timer);
        reject(error);
      }
    });
  }
  
  /**
   * データベース接続をテストする
   * 
   * @param timeoutMs 各クエリのタイムアウト時間（ミリ秒）
   * @returns テスト結果
   */
  public async testConnection(timeoutMs: number = 5000): Promise<DatabaseOperationResult> {
    try {
      // テスト開始時刻を記録
      const testStartTime = Date.now();
      
      // データベース接続前にファイルの存在確認
      try {
        const { checkDbFilesExistence } = await import('../infrastructure/database/databaseService');
        const fileCheck = await checkDbFilesExistence(window.db_path || DB_DIR);
        
        if (!fileCheck.valid) {
          // ファイル確認エラーをログに記録するだけ（接続プロセスは継続）
          console.warn("データベースファイル確認警告:", fileCheck.error);
          console.warn("ファイル確認に失敗しましたが、接続テストを続行します。");
        }
      } catch (fileCheckErr) {
        console.warn("ファイル確認エラー:", fileCheckErr);
        // ファイル確認に失敗しても続行
      }
      
      // データベース接続確認
      if (!this.conn) {
        console.log("接続が存在しないため、新規接続を試みます");
        const connectResult = await this.connect();
        if (!connectResult.success) {
          return connectResult;
        }
      }
      
      const diagnosticResults = {
        basicConnectivity: false,
        showTablesWorks: false,
        nodeQueryWorks: false,
        nodeCount: 0,
        edgeCount: 0,
        tables: [],
        dbPath: window.db_path || 'unknown',
        message: '',
        testDurationMs: 0,
        testedAt: new Date().toISOString(),
        dbMode: '読み取り専用モード', // デフォルトでは読み取り専用
        dbOptions: null as any
      };
      
      // データベースオプションの取得を試行
      try {
        if (this.db && this.db.getOptions) {
          diagnosticResults.dbOptions = this.db.getOptions();
          console.log("データベースオプション:", diagnosticResults.dbOptions);
        }
      } catch (optErr) {
        console.warn("オプション取得エラー:", optErr);
      }
      
      // ステップ1: 基本的な接続テスト
      try {
        console.log("基本的な接続テスト開始...");
        const basicTestQuery = "RETURN 1 AS test";
        const basicResult = await this.executeQueryWithTimeout(basicTestQuery, timeoutMs);
        console.log("基本接続テスト結果:", basicResult);
        
        if (basicResult) {
          diagnosticResults.basicConnectivity = true;
          console.log("✅ 基本接続テスト成功");
          
          try {
            // 結果を確認
            const testObj = await basicResult.getAllObjects();
            console.log("基本テストデータ:", testObj);
            
            if (!testObj || testObj.length === 0 || typeof testObj[0].test === 'undefined') {
              console.warn("基本テスト: 有効なデータが返されていません");
              diagnosticResults.message = "基本接続テスト失敗: 結果が有効なデータを含んでいません";
              return {
                success: false,
                error: diagnosticResults.message,
                data: diagnosticResults
              };
            }
          } catch (dataErr) {
            console.warn("基本テストデータ取得エラー:", dataErr);
            diagnosticResults.message = `基本テストデータ取得エラー: ${dataErr.message}`;
            return {
              success: false,
              error: diagnosticResults.message,
              data: diagnosticResults
            };
          }
        } else {
          diagnosticResults.message = "基本接続テスト失敗: 結果が空";
          return {
            success: false,
            error: diagnosticResults.message,
            data: diagnosticResults
          };
        }
      } catch (basicErr) {
        console.error("基本接続テスト失敗:", basicErr);
        diagnosticResults.message = `基本接続テスト失敗: ${basicErr.message}`;
        
        // 接続状態を更新
        this.connectionState = {
          ...this.connectionState,
          isConnected: false,
          lastTestedAt: Date.now(),
          errorCount: this.connectionState.errorCount + 1
        };
        
        return {
          success: false,
          error: diagnosticResults.message,
          data: diagnosticResults
        };
      }
      
      // ステップ2: テーブル一覧の取得テスト
      try {
        console.log("テーブル一覧取得テスト開始...");
        const showTablesQuery = "SHOW TABLES";
        const tablesResult = await this.executeQueryWithTimeout(showTablesQuery, timeoutMs);
        console.log("テーブル一覧テスト結果:", tablesResult);
        
        diagnosticResults.showTablesWorks = true;
        
        if (tablesResult && tablesResult.getAllObjects) {
          const tables = await tablesResult.getAllObjects();
          console.log("取得されたテーブル:", tables);
          diagnosticResults.tables = tables || [];
        }
      } catch (tablesErr) {
        console.warn("テーブル一覧取得テスト失敗:", tablesErr);
        // テーブル取得に失敗しても次のテストを続行
      }
      
      // ステップ3: ノード数クエリのテスト
      try {
        console.log("ノード数クエリテスト開始...");
        const countNodeQuery = "MATCH (n) RETURN COUNT(n) AS nodeCount";
        const nodeCountResult = await this.executeQueryWithTimeout(countNodeQuery, timeoutMs);
        console.log("ノード数クエリ結果:", nodeCountResult);
        
        diagnosticResults.nodeQueryWorks = true;
        
        if (nodeCountResult && nodeCountResult.getAllObjects) {
          const countData = await nodeCountResult.getAllObjects();
          console.log("ノード数データ:", countData);
          
          if (countData && countData[0] && typeof countData[0].nodeCount !== 'undefined') {
            const count = parseInt(countData[0].nodeCount);
            diagnosticResults.nodeCount = isNaN(count) ? 0 : count;
          }
        }
        
        // エッジ数も取得
        try {
          const countEdgeQuery = "MATCH ()-[r]->() RETURN COUNT(r) AS edgeCount";
          const edgeCountResult = await this.executeQueryWithTimeout(countEdgeQuery, timeoutMs);
          
          if (edgeCountResult && edgeCountResult.getAllObjects) {
            const edgeData = await edgeCountResult.getAllObjects();
            
            if (edgeData && edgeData[0] && typeof edgeData[0].edgeCount !== 'undefined') {
              const count = parseInt(edgeData[0].edgeCount);
              diagnosticResults.edgeCount = isNaN(count) ? 0 : count;
            }
          }
        } catch (edgeErr) {
          console.warn("エッジ数クエリ失敗:", edgeErr);
        }
      } catch (nodeErr) {
        console.warn("ノード数クエリテスト失敗:", nodeErr);
        // ノード数取得に失敗しても診断情報は返す
      }
      
      // テスト時間を計算
      diagnosticResults.testDurationMs = Date.now() - testStartTime;
      
      // 総合診断
      const isReallyConnected = diagnosticResults.basicConnectivity && 
                               (diagnosticResults.showTablesWorks || diagnosticResults.nodeQueryWorks);
      
      // 接続状態を更新
      this.connectionState = {
        isConnected: isReallyConnected,
        lastTestedAt: Date.now(),
        errorCount: isReallyConnected ? 0 : this.connectionState.errorCount + 1,
        dbPath: window.db_path || 'unknown'
      };
      
      if (isReallyConnected) {
        let message = "データベース接続テスト成功";
        
        if (diagnosticResults.nodeCount === 0 && diagnosticResults.tables.length === 0) {
          message += "。ただし、データベースは空か、スキーマが定義されていない可能性があります。";
        } else if (diagnosticResults.nodeCount === 0) {
          message += "。ただし、ノードデータは存在しません。";
        }
        
        message += ` (テスト時間: ${diagnosticResults.testDurationMs}ms)`;
        diagnosticResults.message = message;
        
        return {
          success: true,
          data: diagnosticResults
        };
      } else {
        const message = "データベース接続に問題があります。接続は確立されましたが、クエリが正常に実行できません。" +
                       ` (テスト時間: ${diagnosticResults.testDurationMs}ms)`;
        diagnosticResults.message = message;
        
        return {
          success: false,
          error: diagnosticResults.message,
          data: diagnosticResults
        };
      }
    } catch (error) {
      console.error("データベース接続テストエラー:", error);
      
      // 接続状態を更新
      this.connectionState = {
        ...this.connectionState,
        isConnected: false,
        lastTestedAt: Date.now(),
        errorCount: this.connectionState.errorCount + 1
      };
      
      return {
        success: false,
        error: `データベース接続テストに失敗しました: ${error.message}`,
        data: {
          dbPath: window.db_path || 'unknown',
          message: `接続テスト中にエラーが発生: ${error.message}`,
          testedAt: new Date().toISOString()
        }
      };
    }
  }
  
  /**
   * データベースのノード数とエッジ数を取得する
   * 
   * @returns ノード数とエッジ数
   */
  public async getStats(): Promise<DatabaseOperationResult> {
    try {
      if (!this.conn) {
        return {
          success: false,
          error: "データベース接続がありません"
        };
      }
      
      try {
        // ノード数を取得
        const nodeCountResult = await this.executeDirectQuery("MATCH (n) RETURN COUNT(n) AS nodeCount");
        if (!nodeCountResult.success) {
          return {
            success: false,
            error: nodeCountResult.error || "ノード数の取得に失敗しました"
          };
        }
        
        // エッジ数を取得
        const edgeCountResult = await this.executeDirectQuery("MATCH ()-[r]->() RETURN COUNT(r) AS edgeCount");
        if (!edgeCountResult.success) {
          return {
            success: false,
            error: edgeCountResult.error || "エッジ数の取得に失敗しました"
          };
        }
        
        // 結果を整形
        const nodeCount = nodeCountResult.data && nodeCountResult.data[0] ? 
          parseInt(nodeCountResult.data[0].nodeCount) : 0;
        const edgeCount = edgeCountResult.data && edgeCountResult.data[0] ? 
          parseInt(edgeCountResult.data[0].edgeCount) : 0;
        
        return {
          success: true,
          data: { 
            nodeCount: isNaN(nodeCount) ? 0 : nodeCount, 
            edgeCount: isNaN(edgeCount) ? 0 : edgeCount 
          }
        };
      } catch (queryError) {
        console.error('データベース統計取得クエリエラー:', queryError);
        return {
          success: false,
          error: `統計クエリエラー: ${queryError.message}`
        };
      }
    } catch (error) {
      console.error('データベース統計取得エラー:', error);
      return {
        success: false,
        error: `データベース統計の取得に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * データベース接続を閉じる
   * 
   * @returns 処理結果
   */
  public async disconnect(): Promise<DatabaseOperationResult> {
    try {
      if (!this.conn || !this.db) {
        // 接続状態をリセット
        this.connectionState = {
          isConnected: false,
          lastTestedAt: Date.now(),
          errorCount: 0,
          dbPath: ''
        };
        
        return {
          success: true,
          data: { message: 'データベース接続は既に閉じられています' }
        };
      }
      
      console.log('データベース接続を閉じます...');
      const cleanupError = await cleanupDatabaseResources(this.conn, this.db);
      if (cleanupError) {
        console.error('接続閉じるエラー:', cleanupError);
        
        // 強制的にリソースをクリア
        this.conn = null;
        this.db = null;
        this.kuzu = null;
        window.conn = null;
        window.db = null;
        window.kuzu = null;
        
        // 接続状態をリセット
        this.connectionState = {
          isConnected: false,
          lastTestedAt: Date.now(),
          errorCount: 0,
          dbPath: ''
        };
        
        return {
          success: false,
          error: cleanupError.message
        };
      }
      
      this.conn = null;
      this.db = null;
      this.kuzu = null;
      
      // グローバル変数からも削除
      window.conn = null;
      window.db = null;
      window.kuzu = null;
      
      // 接続状態をリセット
      this.connectionState = {
        isConnected: false,
        lastTestedAt: Date.now(),
        errorCount: 0,
        dbPath: ''
      };
      
      console.log('データベース接続を正常に閉じました');
      
      return {
        success: true,
        data: { message: 'データベース接続を閉じました' }
      };
    } catch (error) {
      console.error('データベース切断エラー:', error);
      
      // エラーが発生してもリソースを強制クリア
      this.conn = null;
      this.db = null;
      this.kuzu = null;
      window.conn = null;
      window.db = null;
      window.kuzu = null;
      
      // 接続状態をリセット
      this.connectionState = {
        isConnected: false,
        lastTestedAt: Date.now(),
        errorCount: 0,
        dbPath: ''
      };
      
      return {
        success: false,
        error: `データベース接続の切断に失敗しました: ${error.message}`
      };
    }
  }
}

// シングルトンインスタンスを作成
export const databaseService = new DatabaseService();