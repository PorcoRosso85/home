/**
 * apiClient.ts
 * 
 * API通信クライアント
 * HTTP経由でリモートサーバーと通信するためのクライアント実装
 */

import { 
  CommonClient, 
  CommandInfo, 
  ApiRequest, 
  ApiResponse 
} from '../../interface/client/types.ts';
import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * API通信クライアント実装
 * ブラウザ環境またはCLIでHTTP経由でサーバーAPIにアクセスするためのクライアント
 */
export class ApiClient implements CommonClient {
  /**
   * APIエンドポイントのベースURL
   */
  private apiBaseUrl: string;
  
  /**
   * キャッシュ有効フラグ
   */
  private useCache: boolean;
  
  /**
   * キャッシュマップ
   */
  private cache: Map<string, {
    data: any;
    expiry: number;
  }> = new Map();
  
  /**
   * コンストラクタ
   * @param apiBaseUrl APIエンドポイントのベースURL (デフォルト: '/api')
   * @param useCache キャッシュを使用するかどうか
   */
  constructor(apiBaseUrl = '/api/', useCache = true) {
    // APIエンドポイントが/で終わることを確認
    this.apiBaseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl : apiBaseUrl + '/';
    this.useCache = useCache;
  }
  
  /**
   * APIリクエストを送信する
   * 
   * @param action アクション名
   * @param params リクエストパラメータ
   * @returns APIレスポンス
   */
  private async sendApiRequest<T = unknown>(
    action: string, 
    params: Record<string, unknown> = {}
  ): Promise<T> {
    // キャッシュキーの生成
    const cacheKey = `${action}:${JSON.stringify(params)}`;
    
    // キャッシュがあれば使用
    if (this.useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (cached.expiry > Date.now()) {
        return cached.data as T;
      }
      // 期限切れの場合はキャッシュを削除
      this.cache.delete(cacheKey);
    }
    
    // リクエストの構築 - 全てのフィールドをトップレベルに配置
    const request: ApiRequest = {
      action,
      ...params
    };
    
    console.log('APIリクエスト送信:', JSON.stringify(request));
    
    // API呼び出し
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
    
    // 成功したレスポンスをキャッシュ (30分)
    if (this.useCache) {
      this.cache.set(cacheKey, {
        data: result.data,
        expiry: Date.now() + (30 * 60 * 1000) // 30分
      });
    }
    
    return result.data as T;
  }
  
  /**
   * キャッシュをクリアする
   */
  clearCache(): void {
    this.cache.clear();
  }
  
  /**
   * キャッシュの有効/無効を設定
   * 
   * @param enabled キャッシュを有効にするかどうか
   */
  setCache(enabled: boolean): void {
    this.useCache = enabled;
    if (!enabled) {
      this.clearCache();
    }
  }
  
  /**
   * 利用可能なコマンドの取得
   * 
   * @returns コマンド情報の配列
   */
  async getAvailableCommands(): Promise<CommandInfo[]> {
    return this.sendApiRequest<CommandInfo[]>('getCommands');
  }
  
  /**
   * コマンドの実行
   * 
   * @param commandName コマンド名
   * @param args コマンド引数
   * @returns 実行結果
   */
  async executeCommand(commandName: string, args: string[]): Promise<unknown> {
    return this.sendApiRequest('executeCommand', {
      options: {
        command: commandName,
        args
      }
    });
  }
  
  /**
   * スキーマの読み込み
   * 
   * @param path スキーマパス
   * @returns スキーマオブジェクト
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    return this.sendApiRequest<FunctionSchema>('loadSchema', { filePath: path });
  }
  
  /**
   * 依存関係グラフの取得
   * 
   * @param rootSchemaPath ルートスキーマパス
   * @returns グラフオブジェクト
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    return this.sendApiRequest<Graph>('getDependencyGraph', { filePath: rootSchemaPath });
  }
  
  /**
   * スキーマリストの取得
   * 
   * @returns スキーマパスの配列
   */
  async getSchemaList(): Promise<string[]> {
    return this.sendApiRequest<string[]>('getSchemaList');
  }
}
