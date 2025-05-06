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
   * データベースに接続する
   * 
   * @returns 接続結果
   */
  public async connect(): Promise<DatabaseOperationResult> {
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
      } else {
        // 最後のテストから一定時間（60秒）経過している場合は接続を確認
        const now = Date.now();
        const timeSinceLastTest = now - this.connectionState.lastTestedAt;
        
        if (timeSinceLastTest > 60000) {
          console.log('接続の最終テストから時間が経過しています。接続確認を実行...');
          try {
            // 軽量なテストクエリを実行
            const testQuery = 'RETURN 1 AS test';
            const testResult = await this.conn.query(testQuery);
            
            if (testResult) {
              console.log('定期的な接続確認成功');
              this.connectionState.lastTestedAt = now;
              this.connectionState.errorCount = 0;
            } else {
              console.warn('定期的な接続確認失敗。再接続が必要です');
              this.connectionState.isConnected = false;
              const reconnectResult = await this.connect();
              if (!reconnectResult.success) {
                return reconnectResult;
              }
            }
          } catch (testErr) {
            console.warn('定期的な接続確認でエラー発生。再接続が必要です', testErr);
            this.connectionState.isConnected = false;
            const reconnectResult = await this.connect();
            if (!reconnectResult.success) {
              return reconnectResult;
            }
          }
        }
      }
      
      // クエリ実行
      console.log(`クエリ実行: ${query}`);
      
      try {
        const queryResult = await this.conn.query(query);
        
        // 結果の変換
        let resultData;
        if (queryResult.getAllObjects) {
          resultData = await queryResult.getAllObjects();
        } else {
          resultData = queryResult;
        }
        
        // 接続状態を更新 (成功)
        this.connectionState.lastTestedAt = Date.now();
        this.connectionState.errorCount = 0;
        
        return {
          success: true,
          data: resultData
        };
      } catch (queryErr) {
        // クエリエラーが接続の問題を示唆する場合は再接続を試みる
        console.error('クエリ実行エラー:', queryErr);
        
        // エラーメッセージを分析して接続問題かどうか判断
        const errorMsg = queryErr.message || '';
        const isConnectionError = errorMsg.includes('connection') || 
                                  errorMsg.includes('timeout') ||
                                  errorMsg.includes('closed') ||
                                  errorMsg.includes('disconnect');
        
        if (isConnectionError) {
          this.connectionState.errorCount++;
          this.connectionState.isConnected = false;
          
          if (this.connectionState.errorCount <= 2) {
            console.log('接続エラーが検出されたため再接続を試みます');
            const reconnectResult = await this.connect();
            if (reconnectResult.success) {
              // 再接続成功の場合は再度クエリを実行
              console.log('再接続成功。クエリを再試行します');
              return await this.executeDirectQuery(query);
            }
          }
        }
        
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