/**
 * baseClient.ts
 * 
 * 共通クライアント基本実装
 * CLI、ブラウザで共通して使用する機能の実装
 */

import { CommonClient, CommandInfo, ClientConfig } from './types.ts';
import { CommandStore, CommandExecutor, CommandResult } from './commands.ts';
import { SchemaDataAccess } from './schemaClient.ts';
import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * 共通クライアント基本実装
 * CLI、ブラウザどちらでも使用できる共通機能
 */
export class BaseClient implements CommonClient {
  protected config: ClientConfig;
  protected commandStore: CommandStore;
  protected schemaAccess: SchemaDataAccess;
  protected commandExecutor?: CommandExecutor;
  
  /**
   * コンストラクタ
   * 
   * @param schemaAccess スキーマアクセス実装
   * @param commandExecutor コマンド実行実装（省略可）
   * @param config クライアント設定
   */
  constructor(
    schemaAccess: SchemaDataAccess,
    commandExecutor?: CommandExecutor,
    config: ClientConfig = {}
  ) {
    this.config = config;
    this.commandStore = new CommandStore();
    this.schemaAccess = schemaAccess;
    this.commandExecutor = commandExecutor;
  }
  
  /**
   * クライアント設定の取得
   */
  getConfig(): ClientConfig {
    return this.config;
  }
  
  /**
   * クライアント設定の更新
   * 
   * @param config 新しい設定（一部のみの指定も可）
   */
  updateConfig(config: Partial<ClientConfig>): void {
    this.config = { ...this.config, ...config };
  }
  
  /**
   * 利用可能なコマンドの取得
   * 
   * @returns コマンド情報の配列
   */
  async getAvailableCommands(): Promise<CommandInfo[]> {
    return this.commandStore.getAllCommands();
  }
  
  /**
   * コマンドの実行
   * 
   * @param commandName コマンド名
   * @param args コマンド引数
   * @returns 実行結果
   */
  async executeCommand(commandName: string, args: string[]): Promise<unknown> {
    if (!this.commandExecutor) {
      throw new Error('コマンド実行機能が初期化されていません');
    }
    
    const result = await this.commandExecutor.execute(commandName, args);
    
    if (!result.success) {
      throw new Error(result.error || 'コマンド実行エラー');
    }
    
    return result.data;
  }
  
  /**
   * スキーマの読み込み
   * 
   * @param path スキーマパス
   * @returns スキーマオブジェクト
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    return this.schemaAccess.loadSchema(path);
  }
  
  /**
   * 依存関係グラフの取得
   * 
   * @param rootSchemaPath ルートスキーマパス
   * @returns グラフオブジェクト
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    return this.schemaAccess.getDependencyGraph(rootSchemaPath);
  }
  
  /**
   * スキーマリストの取得
   * 
   * @returns スキーマパスの配列
   */
  async getSchemaList(): Promise<string[]> {
    return this.schemaAccess.getSchemaList();
  }
  
  /**
   * コマンド登録
   * 
   * @param command 登録するコマンド情報
   */
  registerCommand(command: CommandInfo): void {
    this.commandStore.registerCommand(command);
  }
  
  /**
   * 複数コマンドの一括登録
   * 
   * @param commands 登録するコマンド情報の配列
   */
  registerCommands(commands: CommandInfo[]): void {
    this.commandStore.registerCommands(commands);
  }
}
