#!/usr/bin/env -S nix shell nixpkgs#nodejs_22 --command node --experimental-strip-types

/**
 * CozoDB Time Travel API - インフラストラクチャ層
 * 
 * このファイルはCozoDBとの直接的なやり取りを行うリポジトリ実装を提供します。
 * データベースクエリの実行と低レベルなデータアクセス機能が含まれています。
 */

import { CozoDb } from "cozo-node";

/**
 * ファイルバージョン管理用リレーションの作成
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @returns 処理結果
 */
export async function createFileVersionsRelation(
  db: CozoDb,
  relationName: string = "file_versions"
): Promise<boolean> {
  try {
    const query = `
      :create ${relationName} {
        file_path: String,
        timestamp: String =>
        content: String,
        commit_message: String?
      }
    `;
    
    await db.run(query);
    return true;
  } catch (error) {
    console.error(`リレーション作成エラー: ${error}`);
    return false;
  }
}

/**
 * ファイルバージョンの保存
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param filePath ファイルパス
 * @param content ファイル内容
 * @param timestamp タイムスタンプ (ISO形式、未指定の場合は現在時刻)
 * @param commitMessage コミットメッセージ
 * @returns 処理結果
 */
export async function saveFileVersion(
  db: CozoDb,
  relationName: string,
  filePath: string,
  content: string,
  timestamp?: string,
  commitMessage?: string
): Promise<boolean> {
  try {
    // タイムスタンプが指定されていない場合は現在時刻を使用
    const ts = timestamp || new Date().toISOString();
    
    const query = `
      ?[file_path, content, commit_message] <- [[$file_path, $content, $commit_message]]
      :put ${relationName} {file_path: $file_path, timestamp: $timestamp => content, commit_message}
    `;
    
    const bindVars = {
      file_path: filePath,
      content: content,
      timestamp: ts,
      commit_message: commitMessage || null
    };
    
    await db.run(query, bindVars);
    return true;
  } catch (error) {
    console.error(`ファイルバージョン保存エラー: ${error}`);
    return false;
  }
}

/**
 * 特定時点でのファイル状態の取得
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param filePath ファイルパス (未指定の場合はすべてのファイル)
 * @param timestamp タイムスタンプ (未指定の場合は最新)
 * @returns ファイル状態の配列
 */
export async function getFileVersions(
  db: CozoDb,
  relationName: string,
  filePath?: string,
  timestamp?: string
): Promise<any[]> {
  try {
    let query: string;
    const bindVars: Record<string, any> = {};
    
    if (filePath && timestamp) {
      // 特定ファイルの特定時点のバージョン
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}, 
                                            file_path = $file_path,
                                            timestamp <= $timestamp
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
      bindVars.file_path = filePath;
      bindVars.timestamp = timestamp;
    } else if (filePath) {
      // 特定ファイルの最新バージョン
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}, 
                                            file_path = $file_path
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
      bindVars.file_path = filePath;
    } else if (timestamp) {
      // 全ファイルの特定時点のバージョン
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}, 
                                            timestamp <= $timestamp
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
      bindVars.timestamp = timestamp;
    } else {
      // 全ファイルの最新バージョン
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
    }
    
    const result = await db.run(query, bindVars);
    if (result && result.rows) {
      return result.rows.map(row => ({
        file_path: row[0],
        timestamp: row[1],
        content: row[2],
        commit_message: row[3]
      }));
    }
    
    return [];
  } catch (error) {
    console.error(`ファイルバージョン取得エラー: ${error}`);
    return [];
  }
}

/**
 * ファイルの変更履歴の取得
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param filePath ファイルパス
 * @param limit 取得するバージョン数の上限
 * @returns 変更履歴の配列
 */
export async function getFileHistory(
  db: CozoDb,
  relationName: string,
  filePath: string,
  limit?: number
): Promise<any[]> {
  try {
    let query = `
      ?[timestamp, content, commit_message] := *${relationName}{file_path: $file_path, timestamp, content, commit_message}
      :order -timestamp
    `;
    
    if (limit && limit > 0) {
      query += `\n:limit ${limit}`;
    }
    
    const bindVars = { file_path: filePath };
    const result = await db.run(query, bindVars);
    
    if (result && result.rows) {
      return result.rows.map(row => ({
        file_path: filePath,
        timestamp: row[0],
        content: row[1],
        commit_message: row[2]
      }));
    }
    
    return [];
  } catch (error) {
    console.error(`ファイル履歴取得エラー: ${error}`);
    return [];
  }
}

/**
 * すべてのタイムスタンプの取得
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param filePath 特定のファイルパス (オプション)
 * @returns タイムスタンプの配列
 */
export async function getAllTimestamps(
  db: CozoDb,
  relationName: string,
  filePath?: string
): Promise<string[]> {
  try {
    let query: string;
    const bindVars: Record<string, any> = {};
    
    if (filePath) {
      // 特定ファイルのタイムスタンプを取得
      query = `
        ?[timestamp] := *${relationName}{file_path: $file_path, timestamp}
        :order timestamp
      `;
      bindVars.file_path = filePath;
    } else {
      // すべてのタイムスタンプを取得
      query = `
        ?[timestamp] := *${relationName}{timestamp}
        :distinct
        :order timestamp
      `;
    }
    
    const result = await db.run(query, bindVars);
    if (result && result.rows) {
      return result.rows.map(row => row[0]);
    }
    
    return [];
  } catch (error) {
    console.error(`タイムスタンプ取得エラー: ${error}`);
    return [];
  }
}

/**
 * パターンに一致するファイルパスの取得
 * 
 * @param db CozoDb インスタンス
 * @param relationName リレーション名
 * @param pattern ファイルパスのパターン (例: "src/components/%")
 * @param timestamp 特定の時点 (オプション)
 * @returns 一致するファイルパスの配列
 */
export async function findFilesByPattern(
  db: CozoDb,
  relationName: string,
  pattern: string,
  timestamp?: string
): Promise<any[]> {
  try {
    let query: string;
    const bindVars: Record<string, any> = { pattern: pattern.replace(/%/g, '%') };
    
    if (timestamp) {
      // 特定時点でのパターン一致ファイル
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}, 
                                            file_path =~ $pattern,
                                            timestamp <= $timestamp
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
      bindVars.timestamp = timestamp;
    } else {
      // 最新のパターン一致ファイル
      query = `
        latest_ts[path, max(timestamp)] := *${relationName}{file_path, timestamp}, 
                                            file_path =~ $pattern
        ?[path, timestamp, content, commit_message] := latest_ts[path, timestamp], 
                                                       *${relationName}{file_path: path, timestamp, content, commit_message}
      `;
    }
    
    const result = await db.run(query, bindVars);
    if (result && result.rows) {
      return result.rows.map(row => ({
        file_path: row[0],
        timestamp: row[1],
        content: row[2],
        commit_message: row[3]
      }));
    }
    
    return [];
  } catch (error) {
    console.error(`パターン検索エラー: ${error}`);
    return [];
  }
}
