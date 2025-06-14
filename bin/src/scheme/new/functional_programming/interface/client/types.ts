/**
 * types.ts
 * 
 * CLI、ブラウザで共通して使用する型定義
 * クライアント処理のための共通インターフェースを定義
 */

import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * 共通クライアントインターフェース
 * CLI、ブラウザの両方で使用する共通メソッドを定義
 */
export interface CommonClient {
  /** 利用可能なコマンドの取得 */
  getAvailableCommands(): Promise<CommandInfo[]>;
  
  /** コマンドの実行 */
  executeCommand(commandName: string, args: string[]): Promise<unknown>;
  
  /** スキーマの読み込み */
  loadSchema(path: string): Promise<FunctionSchema>;
  
  /** 依存関係グラフの取得 */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
  
  /** スキーマリストの取得 */
  getSchemaList(): Promise<string[]>;
}

/**
 * コマンド情報
 */
export interface CommandInfo {
  /** コマンド名 */
  name: string;
  
  /** エイリアス */
  aliases?: string[];
  
  /** 説明 */
  description: string;
  
  /** ヘルプテキスト */
  helpText?: string;
}

/**
 * ヘルプ表示オプション
 */
export interface HelpDisplayOptions {
  /** コマンド表示形式 */
  format?: 'text' | 'html' | 'markdown';
  
  /** 詳細表示フラグ */
  detailed?: boolean;
  
  /** カラー表示フラグ (CLI用) */
  colors?: boolean;
}

/**
 * クライアント設定
 */
export interface ClientConfig {
  /** ベースURL (ブラウザ用) */
  baseUrl?: string;
  
  /** 詳細ログ出力フラグ */
  verbose?: boolean;
  
  /** コマンドパス (CLI用) */
  commandPath?: string;
}

/**
 * API通信用のリクエスト型
 */
export interface ApiRequest {
  /** アクション名 */
  action: string;
  
  /** パラメータ */
  params?: Record<string, unknown>;
  
  /** ファイルパス (loadSchema, getDependencyGraphなどで使用) */
  filePath?: string;
  
  /** データ (saveSchemaなどで使用) */
  data?: any;
  
  /** コマンド実行用オプション */
  options?: Record<string, unknown>;
}

/**
 * API通信用のレスポンス型
 */
export interface ApiResponse {
  /** 成功フラグ */
  success: boolean;
  
  /** データペイロード */
  data?: unknown;
  
  /** エラーメッセージ */
  error?: string;
}
