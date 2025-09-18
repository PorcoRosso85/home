/**
 * browserAdapter.ts
 * 
 * ブラウザインターフェースのためのアダプター
 * ブラウザとサーバーAPIの間の通信を担当します
 */

import { BrowserApiClient, FunctionSchema, ApiRequest, ApiResponse } from '../type.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * ブラウザAPIクライアント実装
 * ブラウザ環境からサーバーAPIにアクセスするためのクライアント
 */
export class BrowserApiClientImpl implements BrowserApiClient {
  /**
   * APIエンドポイントのベースURL
   */
  private apiBaseUrl: string;
  
  /**
   * コンストラクタ
   * @param apiBaseUrl APIエンドポイントのベースURL (デフォルト: '/api')
   */
  constructor(apiBaseUrl: string = '/api') {
    this.apiBaseUrl = apiBaseUrl;
  }
  
  /**
   * APIリクエストを送信する
   * 
   * @param action アクション名
   * @param data リクエストデータ
   * @returns APIレスポンス
   */
  private async sendApiRequest<T = any>(action: string, data: Record<string, any> = {}): Promise<T> {
    const request: ApiRequest = {
      action,
      ...data
    };
    
    const response = await fetch(`${this.apiBaseUrl}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`APIリクエストエラー: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json() as ApiResponse;
    
    if (!result.success) {
      throw new Error(`APIエラー: ${result.error || '不明なエラー'}`);
    }
    
    return result.data as T;
  }
  
  /**
   * スキーマをロードする
   * 
   * @param path スキーマのファイルパス
   * @returns ロードされたスキーマ
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    return this.sendApiRequest<FunctionSchema>('loadSchema', { filePath: path });
  }
  
  /**
   * 依存関係グラフを取得する
   * 
   * @param rootSchemaPath ルートスキーマのパス
   * @returns 依存関係グラフ
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    return this.sendApiRequest<Graph>('getDependencyGraph', { filePath: rootSchemaPath });
  }
  
  /**
   * スキーマリストを取得する
   * 
   * @returns スキーマファイルパスのリスト
   */
  async getSchemaList(): Promise<string[]> {
    return this.sendApiRequest<string[]>('getSchemaList');
  }
  
  /**
   * コマンドを実行する
   * 
   * @param commandName コマンド名
   * @param options コマンドオプション
   * @returns 実行結果
   */
  async executeCommand(commandName: string, options: Record<string, any> = {}): Promise<any> {
    return this.sendApiRequest('executeCommand', { 
      options: { 
        command: commandName,
        ...options
      }
    });
  }
  
  /**
   * 利用可能なコマンドリストを取得
   * 
   * @returns コマンド情報のリスト
   */
  async getAvailableCommands(): Promise<Array<{name: string, aliases: string[], description: string}>> {
    return this.sendApiRequest('getCommands');
  }
}

/**
 * ローカルストレージベースのキャッシュマネージャー
 */
export class CacheManager {
  /**
   * キャッシュプレフィックス
   */
  private prefix: string;
  
  /**
   * コンストラクタ
   * @param prefix キャッシュキーのプレフィックス
   */
  constructor(prefix: string = 'func_schema_') {
    this.prefix = prefix;
  }
  
  /**
   * アイテムをキャッシュに保存
   * 
   * @param key キー
   * @param value 値
   * @param ttl TTL（ミリ秒）。0の場合は無期限
   */
  set(key: string, value: any, ttl: number = 0): void {
    const item = {
      value,
      expiry: ttl > 0 ? Date.now() + ttl : 0
    };
    localStorage.setItem(this.prefix + key, JSON.stringify(item));
  }
  
  /**
   * アイテムをキャッシュから取得
   * 
   * @param key キー
   * @returns 値または undefined（期限切れまたは存在しない場合）
   */
  get<T = any>(key: string): T | undefined {
    const item = localStorage.getItem(this.prefix + key);
    if (!item) return undefined;
    
    try {
      const parsed = JSON.parse(item);
      
      // 期限切れチェック
      if (parsed.expiry > 0 && parsed.expiry < Date.now()) {
        this.remove(key);
        return undefined;
      }
      
      return parsed.value as T;
    } catch (e) {
      return undefined;
    }
  }
  
  /**
   * アイテムをキャッシュから削除
   * 
   * @param key キー
   */
  remove(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }
  
  /**
   * キャッシュをクリア
   */
  clear(): void {
    const keysToRemove: string[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.prefix)) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
  }
}

/**
 * キャッシュ対応APIクライアント
 * BrowserApiClientのラッパーで、キャッシュ機能を追加
 */
export class CachedApiClient implements BrowserApiClient {
  private apiClient: BrowserApiClient;
  private cache: CacheManager;
  
  /**
   * コンストラクタ
   * @param apiClient APIクライアント
   * @param cachePrefix キャッシュプレフィックス
   */
  constructor(apiClient: BrowserApiClient, cachePrefix: string = 'func_schema_') {
    this.apiClient = apiClient;
    this.cache = new CacheManager(cachePrefix);
  }
  
  /**
   * スキーマをロードする（キャッシュ対応）
   * 
   * @param path スキーマのファイルパス
   * @returns ロードされたスキーマ
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    const cacheKey = `schema_${path}`;
    const cached = this.cache.get<FunctionSchema>(cacheKey);
    
    if (cached) {
      return cached;
    }
    
    const schema = await this.apiClient.loadSchema(path);
    this.cache.set(cacheKey, schema, 30 * 60 * 1000); // 30分キャッシュ
    return schema;
  }
  
  /**
   * 依存関係グラフを取得する（キャッシュ対応）
   * 
   * @param rootSchemaPath ルートスキーマのパス
   * @returns 依存関係グラフ
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    const cacheKey = `graph_${rootSchemaPath}`;
    const cached = this.cache.get<Graph>(cacheKey);
    
    if (cached) {
      return cached;
    }
    
    const graph = await this.apiClient.getDependencyGraph(rootSchemaPath);
    this.cache.set(cacheKey, graph, 30 * 60 * 1000); // 30分キャッシュ
    return graph;
  }
  
  /**
   * スキーマリストを取得する（キャッシュ対応）
   * 
   * @returns スキーマファイルパスのリスト
   */
  async getSchemaList(): Promise<string[]> {
    const cacheKey = 'schema_list';
    const cached = this.cache.get<string[]>(cacheKey);
    
    if (cached) {
      return cached;
    }
    
    const list = await this.apiClient.getSchemaList();
    this.cache.set(cacheKey, list, 5 * 60 * 1000); // 5分キャッシュ
    return list;
  }
  
  /**
   * キャッシュをクリアする
   */
  clearCache(): void {
    this.cache.clear();
  }
}
