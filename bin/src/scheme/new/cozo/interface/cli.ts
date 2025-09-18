#!/usr/bin/env -S nix shell nixpkgs#nodejs_22 --command node --experimental-strip-types

/**
 * CozoDB Time Travel API - インターフェース層(CLI)
 * 
 * このファイルはTime Travel APIの動作確認を行うためのCLIを提供します。
 * 各ユースケースのテストと結果表示を行います。
 */

import { createTimeTravelRepository } from "../application/timeTravel/api.ts";

/**
 * 結果を整形して表示する
 * 
 * @param title タイトル
 * @param data 表示データ
 * @param indent インデント（オプション）
 */
function displayResult(title: string, data: any, indent: number = 0): void {
  const indentStr = " ".repeat(indent);
  console.log(`${indentStr}${title}:`);
  console.log(`${indentStr}${JSON.stringify(data, null, 2)}`);
  console.log();
}

/**
 * メイン実行関数
 */
async function main(): Promise<void> {
  console.log("===== CozoDB Time Travel API テスト =====\n");

  // リポジトリの作成
  const repo = createTimeTravelRepository();
  
  try {
    console.log("[テスト1] リポジトリの初期化とファイルの追跡");
    
    // リポジトリ初期化
    const initResult = await repo.initialize();
    if (initResult) {
      console.log("✓ リレーション file_versions を作成しました");
    } else {
      console.error("× リレーション作成に失敗しました");
    }
    
    // サンプルデータのセットアップ
    const setupResult = await repo.setupSampleData();
    if (setupResult) {
      console.log("✓ サンプルデータを設定しました");
    } else {
      console.error("× サンプルデータの設定に失敗しました");
    }
    
    // テスト2: 特定時点でのリポジトリ状態の取得
    console.log("\n[テスト2] 特定時点でのリポジトリ状態の取得");
    const repoStateTimestamp = "2023-02-01T00:00:00Z";
    const repoState = await repo.getFiles(undefined, repoStateTimestamp);
    displayResult(`${repoStateTimestamp} 時点のリポジトリ状態`, repoState);
    
    // テスト3: リポジトリ内の全コミットタイムスタンプの取得 (usecase2)
    console.log("[テスト3] リポジトリ内の全コミットタイムスタンプの取得 (usecase2)");
    const allTimestamps = await repo.getAllTimestamps();
    displayResult("コミット履歴", allTimestamps);
    
    // テスト4: 特定ファイルの前バージョンと現バージョンの比較 (usecase1)
    console.log("[テスト4] 特定ファイルの前バージョンと現バージョンの比較 (usecase1)");
    const fromTimestamp = "2023-01-01T10:15:30Z";
    const toTimestamp = "2023-02-15T14:30:10Z";
    const filePath = "src/main.js";
    const versionComparison = await repo.compareVersions(filePath, fromTimestamp, toTimestamp);
    displayResult(`${filePath} の ${fromTimestamp} から ${toTimestamp} までの変更`, versionComparison);
    
    // テスト5: 特定期間内のリポジトリ全体の変更履歴
    console.log("[テスト5] 特定期間内のリポジトリ全体の変更履歴");
    const startTimestamp = "2023-01-15T00:00:00Z";
    const endTimestamp = "2023-03-15T00:00:00Z";
    const periodChanges = await repo.getChangesBetween(startTimestamp, endTimestamp);
    displayResult(`${startTimestamp}から${endTimestamp}までの変更履歴`, periodChanges);
    
    // テスト6: リポジトリ内の特定パターンのファイル検索とその履歴
    console.log("[テスト6] リポジトリ内の特定パターンのファイル検索とその履歴");
    const dirPath = "src/components";
    const dirHistory = await repo.getDirectoryHistory(dirPath);
    displayResult(`${dirPath} ディレクトリ内のファイル変更履歴`, dirHistory);
    
    console.log("===== すべてのテストが成功しました =====");
    
  } catch (error) {
    console.error("エラーが発生しました:", error);
  } finally {
    // リポジトリをクローズ
    repo.close();
  }
}

// メイン関数の実行
main().catch(error => {
  console.error("未捕捉エラー:", error);
  process.exit(1);
});
