// KuzuDBデータブラウザ - シンプル版
// parquetファイルを読み込むためのライト版アプリケーション

import * as logger from '../../common/infrastructure/logger';
import { APP_NAME, APP_VERSION } from '../../common/infrastructure/variables';
// DMLアプリケーションのインポートを追加
import { runDMLDemo } from '../../query/application/dml';

logger.info(`${APP_NAME} Parquet Viewer v${APP_VERSION} - 初期化中...`);

interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}

// ステータス表示関数
function updateStatus(message: StatusMessage): void {
  // 新しいロガーを使用
  switch (message.type) {
    case 'info':
      logger.info(message.text);
      break;
    case 'success':
      logger.info(`✓ ${message.text}`);
      break;
    case 'error':
      logger.error(message.text);
      break;
    case 'loading':
      logger.info(`⟳ ${message.text}`);
      break;
  }
}

// Parquetファイルをfetchしてwasm ファイルシステムに書き込む
async function preloadParquetFiles(kuzu: any) {
  updateStatus({ text: 'Parquetファイルをプリロード中...', type: 'loading' });
  
  // 必要なParquetファイルのリスト
  const parquetFiles = [
    'EntityAggregationView.parquet',
    'RequirementVerification.parquet',
    'LocationURI.parquet',
    'VersionState.parquet',
    'ReferenceEntity.parquet',
    'CodeEntity.parquet',
    'RequirementEntity.parquet',
    'DEPENDS_ON.parquet',
    'VERIFICATION_IS_IMPLEMENTED_BY.parquet',
    'AGGREGATES_CODE.parquet',
    'IS_IMPLEMENTED_BY.parquet',
    'CONTAINS_LOCATION.parquet',
    'HAS_LOCATION.parquet',
    'REQUIREMENT_HAS_LOCATION.parquet',
    'TRACKS_STATE_OF_REF.parquet',
    'USES.parquet',
    'AGGREGATES_REQ.parquet',
    'TRACKS_STATE_OF_REQ.parquet',
    'FOLLOWS.parquet',
    'TRACKS_STATE_OF_CODE.parquet',
    'CONTAINS_CODE.parquet',
    'REFERENCES_CODE.parquet',
    'VERIFIED_BY.parquet',
    'REFERENCES_EXTERNAL.parquet',
    'REFERENCE_HAS_LOCATION.parquet'
  ];
  
  let successCount = 0;
  let failCount = 0;
  
  for (const fileName of parquetFiles) {
    try {
      // HTTPでファイルを取得
      const response = await fetch(`/export_data/${fileName}`);
      if (!response.ok) {
        throw new Error(`HTTPエラー: ${response.status}`);
      }
      
      // バイナリデータを取得
      const fileData = await response.arrayBuffer();
      
      // WASM仮想ファイルシステムに書き込む
      kuzu.FS.writeFile(`/${fileName}`, new Uint8Array(fileData));
      
      successCount++;
      logger.info(`Parquetファイルプリロード成功: ${fileName}`);
    } catch (error) {
      failCount++;
      logger.error(`Parquetファイルプリロード失敗: ${fileName} - ${error.message}`);
      updateStatus({ text: `Parquetファイルプリロード失敗: ${fileName} - ${error.message}`, type: 'error' });
    }
  }
  
  // WASM FSの内容を確認（デバッグ用）
  try {
    const files = kuzu.FS.readdir('/');
    logger.info("WASM FSのファイル一覧:", files);
  } catch (err) {
    logger.error("WASM FSの内容確認エラー:", err);
  }
  
  updateStatus({ 
    text: `Parquetファイルプリロード完了 (${successCount}成功/${failCount}失敗)`, 
    type: failCount > 0 ? 'error' : 'success' 
  });
  
  return successCount > 0;
}

// Kuzuデータベースを初期化する関数
async function initializeDatabase() {
  try {
    updateStatus({ text: 'Kuzu-WASM モジュールを読み込み中...', type: 'loading' });
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../node_modules/kuzu-wasm");
    const kuzu = kuzuWasm.default || kuzuWasm;
    
    // グローバルにkuzuオブジェクトを設定（FS APIのために必要）
    window.kuzu = kuzu;
    
    // ------- 修正: WebAssemblyモジュールの初期化を完了するための待機 -------
    // モジュール初期化が確実に完了するのを待つ
    if (typeof kuzu.onRuntimeInitialized !== 'undefined') {
      logger.info('WebAssemblyモジュールの初期化を待機中...');
      await new Promise(resolve => {
        if (kuzu.calledRun) {
          logger.info('WebAssemblyモジュールはすでに初期化されています');
          resolve(true);
        } else {
          kuzu.onRuntimeInitialized = () => {
            logger.info('WebAssemblyモジュールの初期化が完了しました');
            resolve(true);
          };
        }
      });
    } else {
      // 小さな遅延を入れて、モジュールが完全に初期化されるのを待つ
      logger.info('WebAssemblyモジュールの初期化を確認するための短い遅延を挿入...');
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    // ------- 修正ここまで -------
    
    updateStatus({ text: 'Parquetファイルを仮想ファイルシステムに転送中...', type: 'loading' });
    
    // Parquetファイルをプリロード
    await preloadParquetFiles(kuzu);
    
    updateStatus({ text: 'インメモリデータベースを初期化中...', type: 'loading' });
    
    // インメモリデータベースを作成
    const db = new kuzu.Database("");
    window.db_path = "memory";
    
    // データベース接続の作成
    const conn = new kuzu.Connection(db);
    
    // ------- 修正: 接続が完了したことを確認するためのテスト -------
    try {
      logger.info('データベース接続をテスト中...');
      const testQuery = "RETURN 1 as test";
      const result = await conn.query(testQuery);
      const data = await result.getAllObjects();
      logger.info('データベース接続テスト結果:', data);
      await result.close();
      logger.info('データベース接続テスト成功');
    } catch (error) {
      logger.error('データベース接続テスト失敗:', error);
      throw new Error(`データベース接続テストに失敗しました: ${error.message}`);
    }
    // ------- 修正ここまで -------
    
    updateStatus({ text: 'データベース初期化完了', type: 'success' });
    
    return { kuzu, db, conn };
  } catch (error) {
    const errorMsg = `データベース初期化エラー: ${error.message}`;
    updateStatus({ text: errorMsg, type: 'error' });
    throw error;
  }
}

// Cypherスクリプトからコマンドを正しく抽出する関数
function extractCommands(scriptContent: string): string[] {
  // スクリプトの行を取得
  const lines = scriptContent.split('\n');
  
  let currentCommand = '';
  const commands: string[] = [];
  
  // 各行を処理
  for (let line of lines) {
    // コメント行や空行はスキップ
    if (line.trim().startsWith('--') || line.trim().startsWith('//') || line.trim() === '') {
      continue;
    }
    
    // 現在のコマンドに行を追加
    currentCommand += line.trim() + ' ';
    
    // セミコロンが含まれている場合は、コマンドの終了とみなす
    if (line.trim().endsWith(';')) {
      // セミコロンまでを一つのコマンドとして追加
      commands.push(currentCommand.trim());
      // 次のコマンドのために初期化
      currentCommand = '';
    }
  }
  
  // 最後にセミコロンがない未完了のコマンドが残っている場合も追加
  if (currentCommand.trim()) {
    commands.push(currentCommand.trim());
  }
  
  // 空ではないコマンドのみを返す
  return commands.filter(cmd => cmd.trim() !== '');
}

// Cypherスクリプトファイルを読み込み、実行する関数
async function loadAndExecuteCypherScript(conn: any, scriptPath: string) {
  try {
    updateStatus({ text: `Cypherスクリプトを読み込み中: ${scriptPath}`, type: 'loading' });
    
    // ファイルを取得
    const response = await fetch(scriptPath);
    if (!response.ok) {
      throw new Error(`ファイル読み込みエラー: ${response.status} ${response.statusText}`);
    }
    
    const scriptContent = await response.text();
    logger.info(`読み込まれたCypherスクリプト(${scriptPath}):\n${scriptContent}`);
    updateStatus({ text: `スクリプト読み込み成功: ${scriptPath}`, type: 'info' });
    
    // 改良: 新しい方法でスクリプトをコマンドに分割
    const commands = extractCommands(scriptContent);
    
    logger.info("分割されたコマンド:", commands);
    
    if (commands.length === 0) {
      throw new Error(`スクリプトに有効なコマンドが含まれていません: ${scriptPath}`);
    }
    
    updateStatus({ text: `実行するコマンド数: ${commands.length}`, type: 'info' });
    
    let successCount = 0;
    let failureCount = 0;
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        // 通常のCypherコマンドを実行
        updateStatus({ text: `クエリ実行中: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`, type: 'loading' });
        
        const result = await conn.query(command);
        const resultData = await result.getAllObjects();
        
        // ログにのみデータを出力
        logger.info(`クエリ実行結果:`, command);
        logger.info(resultData);
        
        successCount++;
      } catch (queryError) {
        failureCount++;
        
        logger.error(`クエリ実行エラー: ${queryError.message} (${command})`);
        updateStatus({ text: `クエリ実行エラー: ${queryError.message}`, type: 'error' });
      }
    }
    
    // 結果のサマリーをログにのみ表示
    if (failureCount > 0) {
      // その他のエラー
      updateStatus({ 
        text: `スクリプト実行完了 (${successCount}成功/${failureCount}失敗): 一部のコマンドでエラーが発生しました`, 
        type: 'error' 
      });
    } else {
      // すべて成功
      updateStatus({ 
        text: `スクリプト実行完了: ${scriptPath} (${successCount}コマンド成功)`, 
        type: 'success' 
      });
      
      logger.info(`すべてのクエリが正常に実行されました。`);
    }
    
    return failureCount === 0;
  } catch (error) {
    updateStatus({ text: `スクリプト実行エラー: ${error.message}`, type: 'error' });
    return false;
  }
}

// React関連のimport
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';

// アプリケーション初期化
document.addEventListener("DOMContentLoaded", async () => {
  try {
    logger.info("KuzuDB クエリブラウザ - 開発者版");
    logger.info("kuzu/query ディレクトリのCypherクエリファイルを使用します");
    
    // Reactアプリをマウント
    const rootElement = document.getElementById('root');
    if (rootElement) {
      // @ts-ignore - React/JSXのエラーを無視
      const root = createRoot(rootElement);
      // @ts-ignore - React/JSXのエラーを無視
      root.render(React.createElement(App))
      logger.info('Reactアプリがマウントされました');
    } else {
      logger.error('エラー: rootエレメントが見つかりません。');
    }
    
    // ------- 修正: 実行順序の変更 -------
    // データベース初期化（KuzuとFS APIを含む）を先に行う
    logger.info("データベースとWASM FS初期化中...");
    const { conn } = await initializeDatabase();
    
    // クエリディレクトリのマウント確認テスト
    logger.info("=== クエリディレクトリテスト開始 ===");
    
    // 各クエリディレクトリの確認
    const queryDirs = ['ddl', 'dml', 'dql'];
    for (const dir of queryDirs) {
      try {
        const response = await fetch(`/${dir}/`);
        logger.info(`/${dir}/ ディレクトリ取得: ${response.ok ? '成功' : '失敗'} (${response.status})`);
        if (response.ok) {
          const files = await response.json();
          logger.info(`/${dir}/ 内のファイル:`, files);
          
          // 各ディレクトリ内の最初のCypherファイルを取得してみる
          if (files.length > 0) {
            const firstCypher = files[0];
            try {
              const cypherResponse = await fetch(`/${dir}/${firstCypher}`);
              if (cypherResponse.ok) {
                const content = await cypherResponse.text();
                logger.info(`/${dir}/${firstCypher} の内容:`, content.substring(0, 100) + (content.length > 100 ? '...' : ''));
              }
            } catch (cypherError) {
              logger.error(`/${dir}/${firstCypher} の取得に失敗:`, cypherError);
            }
          }
        }
      } catch (error) {
        logger.info(`/${dir}/ ディレクトリ取得エラー: ${error.message}`);
      }
    }
    
    logger.info("=== クエリディレクトリテスト終了 ===");
    // ------- 修正ここまで -------
    
    // DDL実行とDMLアプリケーション実行
    logger.info("=== DDLファイルの実行開始 ===");
    
    try {
      // ------- 修正: 追加の待機とデータベース接続テスト -------
      // もう一度データベース接続をテスト
      try {
        logger.info('実行前に接続状態をもう一度テスト中...');
        const testQuery = "RETURN 2 as test";
        const result = await conn.query(testQuery);
        const data = await result.getAllObjects();
        logger.info('事前接続テスト結果:', data);
        await result.close();
        logger.info('接続テスト成功、クエリ実行を開始します');
      } catch (error) {
        logger.error('接続テスト失敗:', error);
        throw new Error(`接続テストに失敗しました: ${error.message}`);
      }
      // ------- 修正ここまで -------
      
      // DDLファイルを実行
      updateStatus({ text: 'DDLスキーマファイルを実行中...', type: 'loading' });
      const ddlResponse = await fetch('/ddl/');
      if (ddlResponse.ok) {
        const ddlFiles = await ddlResponse.json();
        logger.info('利用可能なDDLファイル:', ddlFiles);
        
        // スキーマファイルを優先して実行
        for (const file of ddlFiles) {
          if (file.endsWith('_schema.cypher') || file.endsWith('schema.cypher')) {
            logger.info(`DDLスキーマを実行中: ${file}`);
            await loadAndExecuteCypherScript(conn, `/ddl/${file}`);
          }
        }
      }
      
      // DDL実行後、DMLアプリケーションを実行
      try {
        updateStatus({ text: 'DMLアプリケーションを実行中...', type: 'loading' });
        logger.info('DMLアプリケーションの実行を開始します...');
        
        await runDMLDemo(conn);
        
        updateStatus({ text: 'DMLアプリケーション実行完了', type: 'success' });
        logger.info('DMLアプリケーションの実行が完了しました');
      } catch (error) {
        updateStatus({ text: `DMLアプリケーション実行エラー: ${error.message}`, type: 'error' });
        logger.error('DMLアプリケーション実行エラー:', error);
      }
      
      // データ検証
      logger.info("=== データベース検証 ===");
      try {
        const countQuery = "MATCH (n) RETURN count(n) as NodeCount";
        const relCountQuery = "MATCH ()-[r]->() RETURN count(r) as RelCount";
        
        const nodeResult = await conn.query(countQuery);
        const nodeData = await nodeResult.getAllObjects();
        logger.info("ノード数:", nodeData);
        
        const relResult = await conn.query(relCountQuery);
        const relData = await relResult.getAllObjects();
        logger.info("リレーションシップ数:", relData);
        
        updateStatus({ 
          text: `データベースロード完了: ${nodeData[0]?.NodeCount || 0} ノード, ${relData[0]?.RelCount || 0} リレーションシップ`, 
          type: 'success' 
        });
      } catch (verifyError) {
        logger.error("データベース検証エラー:", verifyError);
      }
      
    } catch (error) {
      logger.error("クエリファイル実行エラー:", error);
      updateStatus({ 
        text: `クエリファイルの実行に失敗しました: ${error.message}`, 
        type: 'error' 
      });
    }
    
    logger.info("=== DDLファイルとDMLアプリケーションの実行終了 ===");
    
  } catch (error) {
    logger.error('初期化エラー:', error);
    updateStatus({ text: `初期化中にエラーが発生しました: ${error.message}`, type: 'error' });
  }
  
  logger.info("KuzuDB ブラウザの処理が完了しました。ログを確認してください。");
});

// グローバル定義（TypeScript用）
declare global {
  interface Window {
    db_path: string;
    kuzu: any; // Kuzu WASMオブジェクト
  }
}