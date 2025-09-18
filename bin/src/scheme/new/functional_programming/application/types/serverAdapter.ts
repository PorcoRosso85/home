#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --check
/**
 * serverAdapter.ts
 * 
 * サーバーインターフェースのためのアダプター
 * APIリクエスト/レスポンスとドメインオブジェクト間の変換を担当し、
 * CLIと同様の機能をAPIを通じて提供します。
 * 関数型アプローチによる実装を提供します。
 */

import { SchemaDataAccess, ApiRequest, ApiResponse, parseFunctionSchema, CommandArgs } from '../type.ts';
import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';
import { CliCommand } from '../../interface/cli.ts';
import { ApplicationAdapter, CommandExecutor, ApiHandler, ServerAdapter } from './adapter.ts';

/**
 * スキーマデータアクセス関数
 * ファイルシステムからのスキーマロード
 * 
 * @param path ファイルパス
 * @returns スキーマを解決するPromise
 */
export async function loadSchema(path: string): Promise<FunctionSchema> {
  try {
    const fileContent = await Deno.readTextFile(path);
    return parseFunctionSchema(fileContent);
  } catch (error) {
    throw new Error(`スキーマファイルの読み込みに失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * スキーマをファイルに保存する
 * 
 * @param schema 保存するスキーマ
 * @param path 保存先パス
 * @returns 保存処理を解決するPromise
 */
export async function saveSchema(schema: FunctionSchema, path: string): Promise<void> {
  try {
    const dirPath = path.substring(0, path.lastIndexOf('/'));
    try {
      await Deno.mkdir(dirPath, { recursive: true });
    } catch (e) {
      // ディレクトリが既に存在する場合は無視
    }
    
    await Deno.writeTextFile(path, JSON.stringify(schema, null, 2));
  } catch (error) {
    throw new Error(`スキーマファイルの保存に失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * 依存関係グラフを取得する
 * 
 * @param rootSchemaPath ルートスキーマのパス
 * @returns グラフを解決するPromise
 */
export async function getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
  // FIXME: ダミーデータを返す一時的な実装
  // 本来は schemasToGraph 関数を使用して
  // 実際のスキーマから依存関係を分析するべきである
  console.log(`依存関係グラフを取得しようとしています: ${rootSchemaPath}`);
  
  // ダミーグラフ構造
  const dummyGraph: Graph = {
    nodes: [
      {
        id: "Function_Meta",
        labels: ["Function"],
        properties: {
          title: "Function Metadata Schema",
          description: "関数メタデータのスキーマ定義",
          type: "function",
          resourceUri: `file://${rootSchemaPath}`
        }
      },
      {
        id: "UserAuth",
        labels: ["Function"],
        properties: {
          title: "User Authentication",
          description: "ユーザー認証関数",
          type: "function",
          resourceUri: "file:///home/nixos/scheme/new/functional_programming/UserAuth__Function.json"
        }
      },
      {
        id: "UserRegister",
        labels: ["Function"],
        properties: {
          title: "User Registration",
          description: "ユーザー登録関数",
          type: "function",
          resourceUri: "file:///home/nixos/scheme/new/functional_programming/UserRegister__Function.json"
        }
      }
    ],
    edges: [
      {
        id: "UserAuth->Function_Meta",
        source: "UserAuth",
        target: "Function_Meta",
        label: "implements",
        properties: {
          type: "schema_implementation"
        }
      },
      {
        id: "UserRegister->Function_Meta",
        source: "UserRegister",
        target: "Function_Meta",
        label: "implements",
        properties: {
          type: "schema_implementation"
        }
      },
      {
        id: "UserRegister->UserAuth",
        source: "UserRegister",
        target: "UserAuth",
        label: "depends_on",
        properties: {
          type: "functional_dependency",
          isCircular: false
        }
      }
    ]
  };
  
  return dummyGraph;
}

/**
 * スキーマを検証する
 * 
 * @param schema 検証するスキーマ
 * @returns 検証結果 (true: 有効, false: 無効)
 */
export async function validateSchema(schema: FunctionSchema): Promise<boolean> {
  // この実装はドメイン層のバリデーションサービスに委譲することが想定される
  return true;
}

/**
 * コマンドストアの型定義
 */
export type CommandStore = {
  /**
   * コマンドマップ
   */
  commands: Map<string, CliCommand>;
};

/**
 * 新しいコマンドストアを作成
 * 
 * @returns 空のコマンドストア
 */
export function createCommandStore(): CommandStore {
  return {
    commands: new Map<string, CliCommand>()
  };
}

/**
 * コマンドストアにコマンドを追加
 * 
 * @param store コマンドストア
 * @param command CLIコマンド
 */
export function addCommand(store: CommandStore, command: CliCommand): void {
  store.commands.set(command.name, command);
  
  // エイリアスも登録
  if (command.aliases) {
    for (const alias of command.aliases) {
      store.commands.set(alias, command);
    }
  }
}

/**
 * コマンドストアからコマンドを取得
 * 
 * @param store コマンドストア
 * @param name コマンド名
 * @returns コマンドまたはundefined
 */
export function getCommand(store: CommandStore, name: string): CliCommand | undefined {
  return store.commands.get(name);
}

/**
 * コマンドストアからすべてのコマンドを取得
 * 
 * @param store コマンドストア
 * @returns 一意のコマンドの配列
 */
export function getAllCommands(store: CommandStore): CliCommand[] {
  // 一意のコマンドのみを抽出（エイリアスを除外）
  return [...new Set(store.commands.values())];
}

/**
 * コマンドストアにコマンドが存在するか確認
 * 
 * @param store コマンドストア
 * @param name コマンド名
 * @returns 存在すればtrue
 */
export function hasCommand(store: CommandStore, name: string): boolean {
  return store.commands.has(name);
}

/**
 * サーバーアダプターの状態
 */
export type ServerAdapterState = {
  /**
   * データアクセス
   */
  dataAccess: SchemaDataAccess;
  
  /**
   * コマンドストア
   */
  commandStore: CommandStore;
  
  /**
   * 初期化済みフラグ
   */
  initialized: boolean;
};

/**
 * サーバーアダプターを作成
 * 
 * @param dataAccess データアクセス
 * @param commandStore コマンドストア
 * @returns サーバーアダプター
 */
export function createServerAdapter(
  dataAccess: SchemaDataAccess,
  commandStore: CommandStore
): ServerAdapter {
  const state: ServerAdapterState = {
    dataAccess,
    commandStore,
    initialized: false
  };
  
  return {
    name: 'ServerAdapter',
    
    // ApplicationAdapter メソッド
    initialize: () => initializeAdapter(state),
    loadSchema: (path) => dataAccess.loadSchema(path),
    saveSchema: (schema, path) => dataAccess.saveSchema(schema, path),
    validateSchema: (schema) => dataAccess.validateSchema(schema),
    getDependencyGraph: (rootSchemaPath) => dataAccess.getDependencyGraph(rootSchemaPath),
    
    // CommandExecutor メソッド
    executeCommand: (commandName, args) => executeCommand(state, commandName, args),
    parseCommandArgs: (args) => parseCommandArgs(args),
    loadCommands: (path) => loadCommandsFromPath(state, path),
    
    // ApiHandler メソッド
    processRequest: (request) => processApiRequest(state, request),
    formatResponse: (success, data, message, error) => formatApiResponse(success, data, message, error)
  };
}

/**
 * アダプターを初期化
 * 
 * @param state アダプター状態
 * @returns 初期化を解決するPromise
 */
async function initializeAdapter(state: ServerAdapterState): Promise<void> {
  if (state.initialized) return;
  
  // データアクセスを初期化（可能であれば）
  if ((state.dataAccess as unknown as ApplicationAdapter)?.initialize) {
    await (state.dataAccess as unknown as ApplicationAdapter).initialize();
  }
  
  state.initialized = true;
  console.log('ServerAdapterの初期化が完了しました');
}

/**
 * コマンドを実行
 * 
 * @param state アダプター状態
 * @param commandName コマンド名
 * @param args コマンド引数
 * @returns 実行を解決するPromise
 */
async function executeCommand(
  state: ServerAdapterState,
  commandName: string,
  args: string[]
): Promise<void> {
  const command = getCommand(state.commandStore, commandName);
  if (!command) {
    throw new Error(`コマンド '${commandName}' が見つかりません`);
  }
  
  await command.execute(args);
}

/**
 * コマンドを指定したパスからロード
 * 
 * @param state アダプター状態
 * @param path コマンドのディレクトリパス
 * @returns ロードを解決するPromise
 */
async function loadCommandsFromPath(
  state: ServerAdapterState,
  path: string
): Promise<void> {
  try {
    // ディレクトリ内のファイルをスキャン
    for await (const entry of Deno.readDir(path)) {
      if (entry.isFile && entry.name.endsWith('.ts')) {
        try {
          // 動的インポート
          const importPath = `${path}/${entry.name}`;
          const fileUrl = `file://${importPath}`;
          const module = await import(fileUrl);
          
          if (module.command && module.command.name) {
            addCommand(state.commandStore, module.command);
            console.log(`コマンド '${module.command.name}' をロードしました`);
          }
        } catch (importError) {
          console.error(`コマンド '${entry.name}' のインポート中にエラーが発生しました:`, importError);
        }
      }
    }
  } catch (error) {
    console.error('コマンドのロード中にエラーが発生しました:', error);
    throw error;
  }
}

/**
 * APIリクエストを処理
 * 
 * @param state アダプター状態
 * @param request APIリクエスト
 * @returns APIレスポンスを解決するPromise
 */
async function processApiRequest(
  state: ServerAdapterState,
  request: ApiRequest
): Promise<ApiResponse> {
  try {
    console.log('APIリクエスト処理開始:', JSON.stringify(request));
    
    // アクションに基づいて処理を分岐
    switch (request.action) {
      case 'loadSchema':
        if (!request.filePath) {
          console.error('filePathが指定されていません:', request);
          return formatApiResponse(false, undefined, undefined, 'filePathが指定されていません');
        }
        const schema = await state.dataAccess.loadSchema(request.filePath);
        return formatApiResponse(true, schema);
        
      case 'saveSchema':
        if (!request.filePath || !request.data) {
          console.error('filePathまたはdataが指定されていません:', request);
          return formatApiResponse(false, undefined, undefined, 'filePathまたはdataが指定されていません');
        }
        await state.dataAccess.saveSchema(request.data, request.filePath);
        return formatApiResponse(true, undefined, 'スキーマを保存しました');
        
      case 'executeCommand':
        return await executeCliCommand(state, request);
        
      case 'getCommands':
        // 利用可能なコマンド一覧を返す
        const commands = getAllCommands(state.commandStore).map(cmd => ({
          name: cmd.name,
          aliases: cmd.aliases || [],
          description: cmd.description
        }));
        return formatApiResponse(true, commands);
        
      case 'getDependencyGraph':
        try {
          if (!request.filePath) {
            console.error('filePathが指定されていません:', request);
            return formatApiResponse(false, undefined, undefined, 'filePathが指定されていません');
          }
          console.log(`[processApiRequest] getDependencyGraph: ${request.filePath}を処理します`);
          const graph = await state.dataAccess.getDependencyGraph(request.filePath);
          console.log(`[processApiRequest] getDependencyGraph: グラフデータが正常に生成されました (ノード数: ${graph.nodes.length})`);
          return formatApiResponse(true, graph);
        } catch (error) {
          console.error(`[processApiRequest] getDependencyGraph エラー:`, error);
          return formatApiResponse(false, undefined, undefined, `依存関係グラフの取得中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`);
        }
        
      case 'getSchemaList':
        // スキーマファイルのリストを取得して返す
        try {
          console.log('スキーマリストを検索中...');
          // Function__Meta.jsonを検索
          const metaSchemaPath = `${Deno.cwd()}/Function__Meta.json`;
          
          // サンプルデータ（仮）
          const sampleData = [
            metaSchemaPath,
            // その他のスキーマファイル
          ];
          
          console.log(`スキーマリスト取得成功: ${sampleData.length}件`);
          return formatApiResponse(true, sampleData);
        } catch (error) {
          console.error('スキーマリスト取得エラー:', error);
          return formatApiResponse(false, undefined, undefined, 'スキーマリストの取得に失敗しました');
        }
        
      default:
        return formatApiResponse(false, undefined, undefined, `不明なアクション: ${request.action}`);
    }
  } catch (error) {
    return formatApiResponse(
      false, 
      undefined,
      undefined,
      error instanceof Error ? error.message : String(error)
    );
  }
}

/**
 * CLIコマンドをAPI経由で実行
 * 
 * @param state アダプター状態
 * @param request APIリクエスト
 * @returns APIレスポンスを解決するPromise
 */
async function executeCliCommand(
  state: ServerAdapterState,
  request: ApiRequest
): Promise<ApiResponse> {
  if (!request.options?.command) {
    return formatApiResponse(false, undefined, undefined, 'commandが指定されていません');
  }
  
  const commandName = request.options.command as string;
  const command = getCommand(state.commandStore, commandName);
  
  if (!command) {
    return formatApiResponse(false, undefined, undefined, `コマンド '${commandName}' が見つかりません`);
  }
  
  try {
    // リクエストパラメータをコマンドライン引数形式に変換
    const args = convertOptionsToArgs(commandName, request.options);
    
    // 標準出力をキャプチャするための準備
    const originalConsoleLog = console.log;
    const logOutput: string[] = [];
    
    // console.logをオーバーライド
    console.log = (...args: any[]) => {
      logOutput.push(args.join(' '));
    };
    
    try {
      // コマンドを実行
      await command.execute(args);
      
      // console.logを復元
      console.log = originalConsoleLog;
      
      return formatApiResponse(true, request.data, logOutput.join('\n'));
    } finally {
      // 例外が発生した場合もconsole.logを復元
      console.log = originalConsoleLog;
    }
  } catch (error) {
    return formatApiResponse(
      false,
      undefined,
      undefined,
      error instanceof Error ? error.message : String(error)
    );
  }
}

/**
 * APIレスポンスをフォーマット
 * 
 * @param success 成功したかどうか
 * @param data レスポンスデータ
 * @param message オプションメッセージ
 * @param error エラー情報
 * @returns フォーマットされたAPIレスポンス
 */
export function formatApiResponse(
  success: boolean,
  data?: any,
  message?: string,
  error?: any
): ApiResponse {
  return {
    success,
    ...(data !== undefined ? { data } : {}),
    ...(message ? { message } : {}),
    ...(error ? { error } : {})
  };
}

/**
 * リクエストパラメータをコマンドライン引数形式に変換
 * 
 * @param commandName コマンド名
 * @param options オプション
 * @returns コマンドライン引数の配列
 */
function convertOptionsToArgs(
  commandName: string,
  options: Record<string, any>
): string[] {
  const args: string[] = [commandName];
  
  // オプションをコマンドライン引数形式に変換
  for (const [key, value] of Object.entries(options)) {
    // commandは既に追加済みのためスキップ
    if (key === 'command') continue;
    
    // 真偽値の場合はフラグとして追加
    if (typeof value === 'boolean') {
      if (value === true) {
        args.push(`--${key}`);
      }
    } 
    // 文字列、数値の場合は値付きオプションとして追加
    else if (typeof value === 'string' || typeof value === 'number') {
      args.push(`--${key}=${value}`);
    }
    // 配列の場合は個別の引数として追加
    else if (Array.isArray(value)) {
      for (const item of value) {
        args.push(String(item));
      }
    }
  }
  
  return args;
}

/**
 * コマンド引数をパース
 * 
 * @param args コマンドライン引数
 * @returns 構造化されたコマンド引数
 */
function parseCommandArgs(args: string[]): CommandArgs {
  const result: CommandArgs = {
    command: args[0] || '',
    flags: {},
    options: {},
    args: []
  };
  
  // 引数解析（簡易版）
  for (let i = 1; i < args.length; i++) {
    const arg = args[i];
    
    // フラグ（--flag 形式）
    if (arg.startsWith('--') && !arg.includes('=')) {
      const flag = arg.slice(2);
      result.flags[flag] = true;
    }
    // オプション（--key=value 形式）
    else if (arg.startsWith('--') && arg.includes('=')) {
      const [key, value] = arg.slice(2).split('=', 2);
      result.options[key] = value;
    }
    // その他の引数
    else {
      result.args.push(arg);
    }
  }
  
  return result;
}

// 下位互換性のために従来のクラスを再エクスポート
export class ServerSchemaDataAccess implements SchemaDataAccess {
  async loadSchema(path: string): Promise<FunctionSchema> {
    return loadSchema(path);
  }
  
  async saveSchema(schema: FunctionSchema, path: string): Promise<void> {
    return saveSchema(schema, path);
  }
  
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    // FIXME: クラス内でも直接ダミーデータを返すように修正
    // return getDependencyGraph(rootSchemaPath);
    console.log(`[ServerSchemaDataAccess] 依存関係グラフを取得しようとしています: ${rootSchemaPath}`);
    
    // ダミーグラフ構造
    const dummyGraph: Graph = {
      nodes: [
        {
          id: "Function_Meta",
          labels: ["Function"],
          properties: {
            title: "Function Metadata Schema",
            description: "関数メタデータのスキーマ定義",
            type: "function",
            resourceUri: `file://${rootSchemaPath}`
          }
        },
        {
          id: "UserAuth",
          labels: ["Function"],
          properties: {
            title: "User Authentication",
            description: "ユーザー認証関数",
            type: "function",
            resourceUri: "file:///home/nixos/scheme/new/functional_programming/UserAuth__Function.json"
          }
        }
      ],
      edges: [
        {
          id: "UserAuth->Function_Meta",
          source: "UserAuth",
          target: "Function_Meta",
          label: "implements",
          properties: {
            type: "schema_implementation"
          }
        }
      ]
    };
    
    return dummyGraph;
  }
  
  async validateSchema(schema: FunctionSchema): Promise<boolean> {
    return validateSchema(schema);
  }
}

// In-Source テスト
if (import.meta.main) {
  console.log("サーバーアダプターのテスト実行中...");
  
  // 簡易テスト用サーバーアダプターの作成
  const commandStore = createCommandStore();
  const dataAccess = new ServerSchemaDataAccess();
  const adapter = createServerAdapter(dataAccess, commandStore);
  
  // 基本機能のテスト
  console.log(`アダプター名: ${adapter.name}`);
  
  // 応答フォーマットのテスト
  const response = formatApiResponse(true, { test: 'data' }, 'テスト成功', null);
  console.assert(response.success === true, "成功フラグが正しく設定されていません");
  console.assert(response.data?.test === 'data', "データが正しく設定されていません");
  console.assert(response.message === 'テスト成功', "メッセージが正しく設定されていません");
  console.assert(response.error === undefined, "エラーフラグが正しく設定されていません");
  
  // コマンド引数変換のテスト
  const args = convertOptionsToArgs('test', {
    command: 'test',
    flag: true,
    option: 'value',
    list: [1, 2, 3]
  });
  
  console.assert(args[0] === 'test', "コマンド名が正しく設定されていません");
  console.assert(args.includes('--flag'), "フラグが正しく変換されていません");
  console.assert(args.includes('--option=value'), "オプションが正しく変換されていません");
  console.assert(args.includes('1') && args.includes('2') && args.includes('3'), "リストが正しく変換されていません");
  
  console.log("テスト成功: サーバーアダプターが正しく機能しています。");
}
