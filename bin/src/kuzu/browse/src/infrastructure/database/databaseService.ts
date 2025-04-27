/**
 * Kuzu データベースサービス
 * データベースの初期化と接続管理を担当します
 */

/**
 * 統一されたインターフェースでデータベースとの連携を行うためのモジュール
 */

// WARN: npm呼び出しだとうまくいかないためモジュールを直接指定している
// 注: ここでは実際のインポートは行わず、initializeDatabase内で動的にインポートします

/**
 * データベース初期化の戻り値型
 */
export interface DatabaseInit {
  kuzu: any;
  db: any;
  conn: any;
}

/**
 * データベースエラーの型
 */
export interface DatabaseError {
  code: string;
  message: string;
  stack?: string;
}

/**
 * 初期化結果型
 */
export type DatabaseResult = DatabaseInit | DatabaseError;

/**
 * エラー判定関数
 */
export const isError = (result: DatabaseResult): result is DatabaseError => {
  return 'code' in result && 'message' in result;
};

/**
 * エラー作成関数
 */
export const createError = (code: string, message: string, error?: Error): DatabaseError => {
  return {
    code,
    message,
    stack: error?.stack
  };
};

/**
 * Kuzuデータベースを初期化する
 * @returns DatabaseInit または DatabaseError
 */
export const initializeDatabase = async (): Promise<DatabaseResult> => {
  try {
    console.log('Kuzu-Wasmモジュールのロード開始...');
    
    // Kuzu-Wasmのロード
    // WARN: npm呼び出しだとうまくいかないためモジュールを直接指定している
    const kuzuWasm = await import("../../../node_modules/kuzu-wasm");
    console.log('Kuzu-Wasmモジュールのロード完了');
    
    // Kuzuインスタンス化
    console.log('Kuzuインスタンス化開始...');
    // kuzuWasmモジュールの処理 - デフォルトエクスポートまたはモジュール自体を使用
    const kuzu = kuzuWasm.default || kuzuWasm;
    console.log('Kuzuインスタンス化完了');
    
    // インメモリデータベースの作成
    console.log('データベース作成開始...');
    const db = new kuzu.Database("");
    console.log('データベース作成完了');
    
    // データベース接続の作成
    console.log('データベース接続開始...');
    const conn = new kuzu.Connection(db);
    console.log('データベース接続完了');

    return { kuzu, db, conn };
  } catch (error) {
    console.error('Kuzu初期化エラー:', error);
    return createError(
      'DB_INIT_ERROR',
      `Kuzuの初期化中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * ユーザーテーブルを作成し、初期データを設定する
 * @param conn データベース接続
 * @returns エラーがあればDatabaseError、なければnull
 */
export const setupUserTable = async (conn: any): Promise<DatabaseError | null> => {
  try {
    // 統一されたユーザーテーブルスキーマ
    const createUserTable = "CREATE NODE TABLE User(id INT64, name STRING, country STRING, PRIMARY KEY (id))";
    await conn.query(createUserTable);
    
    // サンプルデータの挿入
    await conn.query(`CREATE (u:User {id: 1, name: 'Alice', country: 'Japan'})`);
    await conn.query(`CREATE (u:User {id: 2, name: 'Bob', country: 'USA'})`);
    
    return null;
  } catch (error) {
    console.error('テーブル作成エラー:', error);
    return createError(
      'TABLE_SETUP_ERROR',
      `ユーザーテーブルの作成中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * CSVからデータをロードする
 * @param conn データベース接続
 * @param kuzu Kuzuインスタンス
 * @param csvPath CSVのパス
 * @returns エラーがあればDatabaseError、なければnull
 */
export const loadCsvData = async (
  conn: any, 
  kuzu: any, 
  csvPath: string = '/remote_data.csv'
): Promise<DatabaseError | null> => {
  try {
    console.log('CSVファイルを読み込み中...');
    const response = await fetch(csvPath);
    const csvData = await response.text();
    console.log(`CSVデータ: ${csvData.substring(0, 100)}...`);
    
    // CSVをkuzu FS領域に書き込む
    if (kuzu.FS) {
      kuzu.FS.writeFile(csvPath, csvData);
      console.log('CSVファイルをkuzu FSに書き込みました');
      
      // CSVデータの読み込み
      // 1. CSVファイルの内容を解析して主キー値を抽出
      const csvLines = csvData.split('\n');
      const headerLine = csvLines[0];
      const dataLines = csvLines.slice(1);
      
      // 2. ヘッダーから主キーのインデックスを特定
      const headers = headerLine.split(',');
      const idIndex = headers.indexOf('id');
      
      if (idIndex >= 0) {
        // 3. CSVから主キー値を抽出
        const primaryKeys = dataLines
          .filter(line => line.trim() !== '')
          .map(line => {
            const values = line.split(',');
            return values[idIndex];
          });
        
        // 4. CSVデータを優先するため、重複する可能性のある既存レコードを削除
        if (primaryKeys.length > 0) {
          const deleteQuery = `MATCH (u:User) WHERE u.id IN [${primaryKeys.join(', ')}] DELETE u`;
          console.log(`重複防止のためのレコード削除: ${deleteQuery}`);
          try {
            await conn.query(deleteQuery);
            console.log('既存の重複レコードを削除しました');
          } catch (deleteError) {
            console.error('既存レコードの削除エラー:', deleteError.message);
            return createError(
              'DELETE_ERROR',
              deleteError.message,
              deleteError
            );
          }
        }
      }
      
      // 5. CSVデータの読み込み
      const loadData = `COPY User FROM '${csvPath}'`;
      console.log(`クエリ実行: ${loadData}`);
      try {
        const loadResult = await conn.query(loadData);
        console.log('CSVデータ読み込み完了:', loadResult);
      } catch (loadError) {
        // エラーメッセージはそのまま出力（ライブラリのエラーを保持）
        console.error('CSVデータ読み込みエラー:', loadError.message);
        return createError(
          'CSV_IMPORT_ERROR',
          loadError.message,
          loadError
        );
      }
      return null;
    } else {
      return createError(
        'FS_NOT_AVAILABLE',
        'kuzu.FSが利用できません。ファイルシステムアクセスをスキップします'
      );
    }
  } catch (error) {
    console.error('CSVデータロードエラー:', error);
    return createError(
      'CSV_LOAD_ERROR',
      `CSVデータの読み込み中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * データベース接続とリソースをクリーンアップする
 * @param conn データベース接続
 * @param db データベースインスタンス
 * @returns エラーがあればDatabaseError、なければnull
 */
export const cleanupDatabaseResources = async (
  conn: any, 
  db: any
): Promise<DatabaseError | null> => {
  try {
    console.log('接続をクローズしています...');
    await conn.close();
    console.log('接続がクローズされました');
    
    await db.close();
    console.log('データベースがクローズされました');
    return null;
  } catch (error) {
    console.error('クリーンアップエラー:', error);
    return createError(
      'CLEANUP_ERROR',
      `データベースリソースのクリーンアップ中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};
