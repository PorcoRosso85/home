// Kuzu-WASM初期化と実行
// Reactアプリケーションのエントリーポイント
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import { DB_CONNECTION } from './infrastructure/variables';

console.log("Kuzu-WASM ESMモジュールを読み込みました");

// Cypherスクリプトファイルを読み込み、実行する関数
async function loadAndExecuteCypherScript(conn: any, scriptPath: string) {
  try {
    console.log(`Cypherスクリプトを読み込み中: ${scriptPath}`);
    
    // ファイルを取得
    const response = await fetch(scriptPath);
    if (!response.ok) {
      throw new Error(`ファイル読み込みエラー: ${response.status} ${response.statusText}`);
    }
    
    const scriptContent = await response.text();
    console.log(`スクリプト読み込み成功: ${scriptPath}`);
    
    // スクリプトを行ごとに分割し、コマンドを抽出
    const commands = scriptContent
      .split(';')
      .map(cmd => cmd.trim())
      .filter(cmd => cmd.length > 0 && !cmd.startsWith('--'));
    
    console.log(`実行するコマンド数: ${commands.length}`);
    
    // 各コマンドを順番に実行
    for (const command of commands) {
      try {
        console.log(`Cypherコマンド実行: ${command.substring(0, 50)}${command.length > 50 ? '...' : ''}`);
        const result = await conn.execute(command);
        console.log('コマンド実行結果:', result);
      } catch (cmdError) {
        console.error(`コマンド実行エラー: ${cmdError.message}`);
        // エラーが発生しても続行
      }
    }
    
    console.log(`スクリプト実行完了: ${scriptPath}`);
    return true;
  } catch (error) {
    console.error(`スクリプト実行エラー: ${error.message}`);
    return false;
  }
}

// DOMが読み込まれたらReactアプリケーションをマウント
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById('root');
  if (container) {
    const root = createRoot(container);
    root.render(React.createElement(App));
    console.log("Reactアプリケーションをマウントしました");
  } else {
    console.error("ルート要素が見つかりません");
  }
});
