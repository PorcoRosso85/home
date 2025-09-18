#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --check
/**
 * adapter.ts
 * 
 * アプリケーションアダプターの型定義
 * CLI、サーバー、ブラウザの各インターフェース間で共通処理を提供するための型を定義します。
 */

import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';
import { CommandArgs, ApiRequest, ApiResponse } from '../type.ts';

/**
 * アプリケーションアダプター基本型
 * すべてのアダプター実装の基本となる型
 */
export type ApplicationAdapter = {
  /**
   * アダプターの名前
   */
  readonly name: string;
  
  /**
   * アダプターの初期化
   */
  initialize(): Promise<void>;
  
  /**
   * スキーマをロードする
   * @param path ファイルパス
   * @returns ロードされたスキーマ
   */
  loadSchema(path: string): Promise<FunctionSchema>;
  
  /**
   * スキーマを保存する
   * @param schema 保存するスキーマ
   * @param path 保存先パス
   */
  saveSchema(schema: FunctionSchema, path: string): Promise<void>;
  
  /**
   * スキーマを検証する
   * @param schema 検証するスキーマ
   * @returns 検証結果 (true: 有効, false: 無効)
   */
  validateSchema(schema: FunctionSchema): Promise<boolean>;
  
  /**
   * 依存関係グラフを取得する
   * @param rootSchemaPath ルートスキーマのパス
   * @returns 依存関係グラフ
   */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
};

/**
 * コマンド実行インターフェース
 * コマンド実行をサポートするアダプター用の拡張型
 */
export type CommandExecutor = {
  /**
   * コマンドを実行する
   * @param commandName コマンド名
   * @param args コマンド引数
   * @returns 実行結果
   */
  executeCommand(commandName: string, args: string[]): Promise<void>;
  
  /**
   * コマンド引数を解析する
   * @param args 生のコマンド引数配列
   * @returns 構造化されたコマンド引数
   */
  parseCommandArgs(args: string[]): CommandArgs;
  
  /**
   * 指定したパスでコマンドを動的にロードする
   * @param path コマンドを含むディレクトリパス
   */
  loadCommands(path: string): Promise<void>;
};

/**
 * API通信インターフェース
 * API経由でのデータアクセスをサポートするアダプター用の拡張型
 */
export type ApiHandler = {
  /**
   * APIリクエストを処理する
   * @param request APIリクエスト
   * @returns APIレスポンス
   */
  processRequest(request: ApiRequest): Promise<ApiResponse>;
  
  /**
   * APIレスポンスをフォーマットする
   * @param success 成功したかどうか
   * @param data レスポンスデータ
   * @param message オプションメッセージ
   * @param error エラー情報
   * @returns フォーマットされたAPIレスポンス
   */
  formatResponse(success: boolean, data?: any, message?: string, error?: any): ApiResponse;
};

/**
 * サーバーアダプター拡張型
 * CLIとAPIの両方の機能を提供する統合アダプター型
 */
export type ServerAdapter = ApplicationAdapter & CommandExecutor & ApiHandler;

// In-Source テスト
if (import.meta.main) {
  console.log("アダプター型定義のテスト実行中...");
  
  // 型の整合性テスト
  const testAdapter: ApplicationAdapter = {
    name: "TestAdapter",
    async initialize() { console.log("初期化"); },
    async loadSchema(_path) { return {} as FunctionSchema; },
    async saveSchema(_schema, _path) { /* noop */ },
    async validateSchema(_schema) { return true; },
    async getDependencyGraph(_rootSchemaPath) { return { nodes: [], edges: [] }; }
  };
  
  console.log(`アダプター名: ${testAdapter.name}`);
  console.assert(testAdapter.name === "TestAdapter", "アダプター名が正しく設定されていません");
  
  // 複合型のテスト
  type TestAdapter = ApplicationAdapter & ApiHandler;
  const combinedAdapter: TestAdapter = {
    ...testAdapter,
    async processRequest(_request) { return { success: true }; },
    formatResponse(success, data, message, error) {
      return { 
        success, 
        ...(data !== undefined ? { data } : {}),
        ...(message ? { message } : {}),
        ...(error ? { error } : {})
      };
    }
  };
  
  console.log("テスト成功: 型定義が正しく機能しています。");
}
