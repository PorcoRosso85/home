// kuzu/browse/rpc/client.ts

/**
 * 最小構成のJSON-RPC 2.0クライアント
 */

// 単純化したリクエスト型定義
interface RPCRequest {
  jsonrpc: string;
  id: string;
  method: string;
  params?: any;
}

/**
 * 最小機能のRPCクライアント
 */
export class RPCClient {
  private baseUrl: string;

  /**
   * コンストラクタ
   * @param baseUrl RPCサーバーのURL
   */
  constructor(baseUrl: string = "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }

  /**
   * コマンドを実行する（最小構成）
   * @param command 実行するコマンド
   * @param args コマンド引数
   * @returns Promise<void>
   */
  async execute(command: string, args: string[] = []): Promise<void> {
    console.log(`実行: ${command} ${args.join(' ')}`);
    
    // リクエストを構築
    const request: RPCRequest = {
      jsonrpc: "2.0",
      id: Date.now().toString(),
      method: "execute",
      params: {
        command,
        args
      }
    };

    try {
      // コンソールにリクエスト内容を表示（実際のAPIコールはなし）
      console.log("送信するJSONリクエスト:", JSON.stringify(request, null, 2));
      console.log("URL:", `${this.baseUrl}/rpc`);
      console.log("注: 実際のAPIコールは行っていません（デバッグ用）");
    } catch (error) {
      console.error("エラー:", error);
    }
  }
}

// デフォルトエクスポート
export default RPCClient;
