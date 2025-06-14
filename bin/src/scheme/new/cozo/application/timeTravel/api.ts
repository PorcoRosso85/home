#!/usr/bin/env -S nix shell nixpkgs#nodejs_22 --command node --experimental-strip-types

/**
 * CozoDB Time Travel API - アプリケーション層
 * 
 * このファイルは高レベルAPIインターフェースを提供し、
 * ドメイン層とインフラ層の機能を統合します。
 */

import { CozoDb } from "cozo-node";
import * as service from "../../domain/timeTravel/service";
import * as repo from "../../infrastructure/timeTravel/repository";

/**
 * TimeTravelリポジトリ操作用のクラス
 * (実装はすべて内部関数に委譲)
 */
export class TimeTravelRepository {
  private db: CozoDb;
  private relationName: string;

  /**
   * コンストラクタ
   * 
   * @param db CozoDb インスタンス
   * @param relationName リレーション名
   */
  constructor(db: CozoDb, relationName: string = "file_versions") {
    this.db = db;
    this.relationName = relationName;
  }

  /**
   * リポジトリの初期化
   * 
   * @returns 初期化結果
   */
  async initialize(): Promise<boolean> {
    return await repo.createFileVersionsRelation(this.db, this.relationName);
  }

  /**
   * サンプルデータの設定
   * 
   * @returns 設定結果
   */
  async setupSampleData(): Promise<boolean> {
    return await service.setupSampleRepository(this.db, this.relationName);
  }

  /**
   * ファイルバージョンの保存 (usecase1のタイムスタンプ自動管理を含む)
   * 
   * @param filePath ファイルパス
   * @param content ファイル内容
   * @param commitMessage コミットメッセージ
   * @param timestamp タイムスタンプ（オプション、指定しない場合は現在時刻）
   * @returns 保存結果
   */
  async saveFile(
    filePath: string,
    content: string,
    commitMessage: string,
    timestamp?: string
  ): Promise<boolean> {
    // ISO形式のタイムスタンプを使用（未指定時は自動生成）
    return await repo.saveFileVersion(
      this.db,
      this.relationName,
      filePath,
      content,
      timestamp,
      commitMessage
    );
  }

  /**
   * 特定時点でのファイル状態の取得
   * 
   * @param filePath 特定のファイルパス（オプション）
   * @param timestamp 特定の時点（オプション）
   * @returns ファイル情報の配列
   */
  async getFiles(filePath?: string, timestamp?: string): Promise<any[]> {
    return await repo.getFileVersions(
      this.db,
      this.relationName,
      filePath,
      timestamp
    );
  }

  /**
   * リポジトリ内の全タイムスタンプを取得 (usecase2)
   * 
   * @param filePath 特定のファイルパス（オプション）
   * @returns タイムスタンプの配列
   */
  async getAllTimestamps(filePath?: string): Promise<string[]> {
    return await repo.getAllTimestamps(this.db, this.relationName, filePath);
  }

  /**
   * ファイルの前バージョンと現バージョンの比較 (usecase1の比較機能)
   * 
   * @param filePath ファイルパス
   * @param fromTimestamp 前バージョンのタイムスタンプ
   * @param toTimestamp 現バージョンのタイムスタンプ（オプション、未指定時は最新）
   * @returns 比較結果
   */
  async compareVersions(
    filePath: string,
    fromTimestamp: string,
    toTimestamp?: string
  ): Promise<any> {
    return await service.compareFileVersions(
      this.db,
      this.relationName,
      filePath,
      fromTimestamp,
      toTimestamp
    );
  }

  /**
   * 特定期間内の変更を検出
   * 
   * @param startTimestamp 開始時点
   * @param endTimestamp 終了時点（オプション、未指定時は現在）
   * @returns 変更リスト
   */
  async getChangesBetween(
    startTimestamp: string,
    endTimestamp?: string
  ): Promise<any[]> {
    return await service.detectChangesInPeriod(
      this.db,
      this.relationName,
      startTimestamp,
      endTimestamp
    );
  }

  /**
   * ファイルの変更履歴を取得
   * 
   * @param filePath ファイルパス
   * @param limit 取得するバージョン数の上限
   * @returns 変更履歴
   */
  async getFileHistory(filePath: string, limit?: number): Promise<any[]> {
    return await repo.getFileHistory(
      this.db,
      this.relationName,
      filePath,
      limit
    );
  }

  /**
   * 特定パターンに一致するファイルを取得
   * 
   * @param pattern ファイルパスのパターン（例：'src/components/%'）
   * @param timestamp 特定の時点（オプション）
   * @returns 一致するファイル情報
   */
  async findFiles(pattern: string, timestamp?: string): Promise<any[]> {
    return await repo.findFilesByPattern(
      this.db,
      this.relationName,
      pattern,
      timestamp
    );
  }

  /**
   * 特定ディレクトリ内のファイル変更履歴を取得
   * 
   * @param dirPath ディレクトリパス
   * @returns ディレクトリ内のファイルとその変更履歴
   */
  async getDirectoryHistory(dirPath: string): Promise<any[]> {
    return await service.getDirectoryHistory(
      this.db,
      this.relationName,
      dirPath
    );
  }

  /**
   * データベース接続を閉じる
   */
  close(): void {
    this.db.close();
  }
}

/**
 * TimeTravelリポジトリのファクトリ関数
 * 
 * @param relationName リレーション名（オプション）
 * @returns TimeTravelRepositoryインスタンス
 */
export function createTimeTravelRepository(relationName?: string): TimeTravelRepository {
  const db = new CozoDb();
  return new TimeTravelRepository(db, relationName);
}

/**
 * 日付範囲のバリデーション
 * ISO形式の日付文字列か検証し、無効な場合はエラーをスロー
 * 
 * @param timestamp タイムスタンプ文字列
 * @returns 検証済みのタイムスタンプ文字列
 */
export function validateTimestamp(timestamp: string): string {
  // ISO形式の日付をチェック - 正規表現を使用
  const isoPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;
  
  if (!isoPattern.test(timestamp)) {
    throw new Error(`無効なタイムスタンプ形式: ${timestamp}（ISO 8601形式である必要があります）`);
  }
  
  // 日付として解析できるか確認
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) {
    throw new Error(`無効な日付: ${timestamp}`);
  }
  
  return timestamp;
}

/**
 * 現在のISO形式タイムスタンプを取得
 * 
 * @returns 現在時刻のISO形式タイムスタンプ
 */
export function getCurrentTimestamp(): string {
  return new Date().toISOString();
}
