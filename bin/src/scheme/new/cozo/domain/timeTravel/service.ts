#!/usr/bin/env -S nix shell nixpkgs#nodejs_22 --command node --experimental-strip-types

/**
 * CozoDB Time Travel API - ドメイン層
 * 
 * このファイルはTime Travelに関するビジネスロジックを提供します。
 * タイムスタンプの管理、バージョン比較、ファイル内容の差分等の処理が含まれています。
 */

import { CozoDb } from "cozo-node";
import * as repo from "../../infrastructure/timeTravel/repository";

/**
 * ファイル内容の差分を行単位で計算する
 * 
 * @param oldContent 古い内容
 * @param newContent 新しい内容
 * @returns 差分情報の配列
 */
export function calculateDiff(oldContent: string, newContent: string): any[] {
  const oldLines = oldContent.split("\n");
  const newLines = newContent.split("\n");
  const diff: any[] = [];
  
  // 単純な行単位の差分計算（実際のプロダクションでは高度な差分アルゴリズムを使用すべき）
  const maxLen = Math.max(oldLines.length, newLines.length);
  
  for (let i = 0; i < maxLen; i++) {
    if (i >= oldLines.length) {
      // 追加された行
      diff.push({
        type: "追加",
        line: i + 1,
        content: newLines[i]
      });
    } else if (i >= newLines.length) {
      // 削除された行
      diff.push({
        type: "削除",
        line: i + 1,
        content: oldLines[i]
      });
    } else if (oldLines[i] !== newLines[i]) {
      // 変更された行
      diff.push({
        type: "変更",
        line: i + 1,
        old: oldLines[i],
        new: newLines[i]
      });
    } else {
      // 変更なしの行
      diff.push({
        type: "変更なし",
        line: i + 1,
        content: oldLines[i]
      });
    }
  }
  
  return diff;
}

/**
 * ファイルの前バージョンと現バージョンの比較
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param filePath ファイルパス
 * @param fromTimestamp 前バージョンのタイムスタンプ
 * @param toTimestamp 現バージョンのタイムスタンプ (未指定の場合は最新)
 * @returns 比較結果オブジェクト
 */
export async function compareFileVersions(
  db: CozoDb,
  relationName: string,
  filePath: string,
  fromTimestamp: string,
  toTimestamp?: string
): Promise<any> {
  // 前バージョンの取得
  const fromVersions = await repo.getFileVersions(db, relationName, filePath, fromTimestamp);
  if (!fromVersions || fromVersions.length === 0) {
    throw new Error(`${fromTimestamp}時点のバージョンが見つかりません: ${filePath}`);
  }
  const fromVersion = fromVersions[0];
  
  // 現バージョンの取得
  let toVersion;
  if (toTimestamp) {
    const toVersions = await repo.getFileVersions(db, relationName, filePath, toTimestamp);
    if (!toVersions || toVersions.length === 0) {
      throw new Error(`${toTimestamp}時点のバージョンが見つかりません: ${filePath}`);
    }
    toVersion = toVersions[0];
  } else {
    const latestVersions = await repo.getFileVersions(db, relationName, filePath);
    if (!latestVersions || latestVersions.length === 0) {
      throw new Error(`最新バージョンが見つかりません: ${filePath}`);
    }
    toVersion = latestVersions[0];
  }
  
  // 差分を計算
  const diff = calculateDiff(fromVersion.content, toVersion.content);
  
  // 結果を返す
  return {
    file_path: filePath,
    変更前: fromVersion,
    変更後: toVersion,
    diff: diff
  };
}

/**
 * 特定期間内での変更を検出する
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param startTimestamp 開始タイムスタンプ
 * @param endTimestamp 終了タイムスタンプ (未指定の場合は現在)
 * @returns 変更のリスト
 */
export async function detectChangesInPeriod(
  db: CozoDb,
  relationName: string,
  startTimestamp: string,
  endTimestamp?: string
): Promise<any[]> {
  // 開始時点でのファイル一覧
  const startFiles = await repo.getFileVersions(db, relationName, undefined, startTimestamp);
  
  // 終了時点での（または最新の）ファイル一覧
  const endFiles = endTimestamp 
    ? await repo.getFileVersions(db, relationName, undefined, endTimestamp)
    : await repo.getFileVersions(db, relationName);
  
  const changes: any[] = [];
  
  // 各ファイルごとに変更があったかチェック
  for (const endFile of endFiles) {
    const startFile = startFiles.find(f => f.file_path === endFile.file_path);
    
    if (!startFile) {
      // 新規作成されたファイル
      changes.push({
        timestamp: endFile.timestamp,
        file_path: endFile.file_path,
        commit_message: endFile.commit_message,
        change_type: "追加",
        content: endFile.content
      });
    } else if (startFile.content !== endFile.content) {
      // 内容が変更されたファイル
      const diff = calculateDiff(startFile.content, endFile.content);
      const addedLines = diff.filter(d => d.type === "追加").length;
      const deletedLines = diff.filter(d => d.type === "削除").length;
      const changedLines = diff.filter(d => d.type === "変更").length;
      
      // 簡易的な関数検出（実際のプロダクションではより堅牢な方法を使用すべき）
      const funcRegex = /function\s+(\w+)/g;
      const oldFuncs = [...startFile.content.matchAll(funcRegex)].map(m => m[1]);
      const newFuncs = [...endFile.content.matchAll(funcRegex)].map(m => m[1]);
      const addedFuncs = newFuncs.filter(f => !oldFuncs.includes(f));
      
      changes.push({
        timestamp: endFile.timestamp,
        file_path: endFile.file_path,
        commit_message: endFile.commit_message,
        change_type: "変更",
        changed_lines: changedLines + addedLines + deletedLines,
        added_functions: addedFuncs
      });
    }
  }
  
  // 削除されたファイルを検出
  for (const startFile of startFiles) {
    const endFile = endFiles.find(f => f.file_path === startFile.file_path);
    if (!endFile) {
      changes.push({
        timestamp: endTimestamp || new Date().toISOString(),
        file_path: startFile.file_path,
        commit_message: "ファイル削除",
        change_type: "削除"
      });
    }
  }
  
  // 変更日時でソート
  return changes.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

/**
 * 特定ディレクトリ内のファイル変更履歴を取得
 * 
 * @param db CozoDb インスタンス 
 * @param relationName リレーション名
 * @param dirPath ディレクトリパス
 * @returns ディレクトリ内のファイルとその変更履歴
 */
export async function getDirectoryHistory(
  db: CozoDb,
  relationName: string,
  dirPath: string
): Promise<any[]> {
  // パターンマッチングでディレクトリ内のファイルを検索
  const pattern = `${dirPath}/%`;
  const files = await repo.findFilesByPattern(db, relationName, pattern);
  
  const result = [];
  
  // 各ファイルについて履歴を取得
  for (const file of files) {
    const history = await repo.getFileHistory(db, relationName, file.file_path);
    result.push({
      file_path: file.file_path,
      commits: history.map(h => ({
        timestamp: h.timestamp,
        commit_message: h.commit_message
      }))
    });
  }
  
  return result;
}

/**
 * 初期状態のセットアップ - サンプルファイルとバージョンを作成
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @returns 処理結果
 */
export async function setupSampleRepository(
  db: CozoDb,
  relationName: string = "file_versions"
): Promise<boolean> {
  try {
    // リレーションを作成
    await repo.createFileVersionsRelation(db, relationName);
    
    // ファイル1の初期バージョン
    await repo.saveFileVersion(
      db,
      relationName,
      "src/main.js",
      "// Initial version\nfunction main() {\n  console.log('Hello world');\n}\n",
      "2023-01-01T10:15:30Z",
      "Initial commit"
    );
    
    // ファイル2の初期バージョン
    await repo.saveFileVersion(
      db,
      relationName,
      "src/utils.js",
      "// Utility functions\nfunction formatDate(date) {\n  return date.toISOString();\n}\n",
      "2023-01-01T10:20:45Z",
      "Add utility functions"
    );
    
    // ファイル3の初期バージョン
    await repo.saveFileVersion(
      db,
      relationName,
      "src/components/Header.js",
      "function Header() {\n  return '<header>My App</header>';\n}\n",
      "2023-01-01T11:05:22Z",
      "Add Header component"
    );
    
    // ファイル1の更新バージョン
    await repo.saveFileVersion(
      db,
      relationName,
      "src/main.js",
      "// Updated version\nfunction main() {\n  console.log('Hello world');\n  initApp();\n  setupEventListeners();\n}\n\nfunction initApp() {\n  // Initialize application\n}\n",
      "2023-02-15T14:30:10Z",
      "Update main.js with new features"
    );
    
    // ファイル2の更新バージョン
    await repo.saveFileVersion(
      db,
      relationName,
      "src/utils.js",
      "// Utility functions - refactored\nfunction formatDate(date) {\n  return date.toISOString();\n}\n\nfunction parseJSON(str) {\n  try {\n    return JSON.parse(str);\n  } catch (e) {\n    return null;\n  }\n}\n\nfunction deepClone(obj) {\n  return JSON.parse(JSON.stringify(obj));\n}\n",
      "2023-03-10T09:45:18Z",
      "Refactor utils.js"
    );
    
    return true;
  } catch (error) {
    console.error(`サンプルリポジトリ作成エラー: ${error}`);
    return false;
  }
}
