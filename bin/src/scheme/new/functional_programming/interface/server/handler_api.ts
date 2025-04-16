#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-net --allow-read --check
/**
 * 統合APIハンドラー
 * 
 * コマンド駆動型APIエンドポイントを提供するハンドラー
 */

import { ApiRequest, ApiResponse } from '../../application/type.ts';
import { createCommandStore, createServerAdapter, ServerSchemaDataAccess } from '../../application/types/serverAdapter.ts';
import { loadCommands } from './commandLoader.ts';

// コマンドストアの初期化
const commandStore = createCommandStore();

// データアクセスの初期化
const dataAccess = new ServerSchemaDataAccess();

// サーバーアダプターの作成
const serverAdapter = createServerAdapter(dataAccess, commandStore);

// 初期化済みフラグ
let initialized = false;

/**
 * APIリクエストハンドラー
 * @param req HTTPリクエスト
 * @returns HTTPレスポンス
 */
export async function handleApiRequest(req: Request): Promise<Response> {
  // アダプターが未初期化の場合は初期化
  if (!initialized) {
    try {
      // アダプターを初期化
      await serverAdapter.initialize();
      
      // コマンドをロード
      const commands = await loadCommands();
      commands.forEach(command => {
        // 関数ベースのAPIを使用してコマンドを追加
        commandStore.commands.set(command.name, command);
        
        // エイリアスも登録
        if (command.aliases) {
          for (const alias of command.aliases) {
            commandStore.commands.set(alias, command);
          }
        }
      });
      
      initialized = true;
    } catch (error) {
      console.error('APIハンドラーの初期化中にエラーが発生しました:', error);
      return createErrorResponse('サーバーの初期化に失敗しました', 500);
    }
  }
  
  try {
    // リクエストボディを解析
    let requestData: ApiRequest;
    try {
      const requestText = await req.text();
      console.log('受信APIリクエスト:', requestText);
      
      try {
        requestData = JSON.parse(requestText) as ApiRequest;
      } catch (parseError) {
        console.error('JSONパースエラー:', parseError);
        return createErrorResponse('リクエストJSONのパースに失敗しました', 400);
      }
      
      console.log('パース後リクエスト:', requestData);
    } catch (error) {
      console.error('リクエスト読み取りエラー:', error);
      return createErrorResponse('リクエストボディの読み取りに失敗しました', 400);
    }
    
    // サーバーアダプターにリクエストを処理させる
    const response = await serverAdapter.processRequest(requestData);
    
    // レスポンスを返す
    return new Response(JSON.stringify(response), {
      status: response.success ? 200 : 400,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    // 例外発生時のエラーレスポンス
    return createErrorResponse(
      error instanceof Error ? error.message : String(error),
      500
    );
  }
}

/**
 * エラーレスポンスを作成
 * 
 * @param errorMessage エラーメッセージ
 * @param statusCode ステータスコード
 * @returns エラーレスポンス
 */
function createErrorResponse(errorMessage: string, statusCode: number): Response {
  const errorResponse: ApiResponse = {
    success: false,
    error: errorMessage
  };
  
  return new Response(JSON.stringify(errorResponse), {
    status: statusCode,
    headers: { 'Content-Type': 'application/json' }
  });
}

// In-Source テスト
if (import.meta.main) {
  console.log("APIハンドラーのテスト実行中...");
  
  // モックリクエストの作成
  const createMockRequest = (body: any): Request => {
    return new Request("http://localhost/api", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });
  };
  
  // テストケース
  const testCases = [
    {
      name: "ステータス取得",
      request: createMockRequest({ action: "getCommands" }),
      expectedStatus: 200
    },
    {
      name: "不正なアクション",
      request: createMockRequest({ action: "invalidAction" }),
      expectedStatus: 400
    },
    {
      name: "不正なリクエスト",
      request: new Request("http://localhost/api", { method: "POST", body: "invalid json" }),
      expectedStatus: 400
    }
  ];
  
  // テストの実行
  (async () => {
    for (const testCase of testCases) {
      try {
        const response = await handleApiRequest(testCase.request);
        console.assert(
          response.status === testCase.expectedStatus,
          `テスト "${testCase.name}" 失敗: ステータスコードが ${response.status} ですが、${testCase.expectedStatus} が期待されていました`
        );
        console.log(`テスト "${testCase.name}" 成功: ステータスコード ${response.status}`);
      } catch (error) {
        console.error(`テスト "${testCase.name}" エラー:`, error);
      }
    }
    
    console.log("テスト完了");
  })();
}

