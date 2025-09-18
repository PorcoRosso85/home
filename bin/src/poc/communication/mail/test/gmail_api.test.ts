/**
 * Gmail APIクライアントのテスト
 * 参考: n8n/packages/nodes-base/nodes/Google/Gmail/test/v2/GmailV2.node.test.ts
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { GmailClient } from "../infrastructure/gmail_client.ts";
import type { Email, MailFetchOptions } from "../types.ts";

// n8nテストパターン: APIレスポンスのモック（GmailV2.node.test.ts）
const mockMessageList = {
  messages: [
    { id: "msg1", threadId: "thread1" },
    { id: "msg2", threadId: "thread2" }
  ],
  resultSizeEstimate: 2
};

const mockMessageDetail = {
  id: "msg1",
  threadId: "thread1",
  labelIds: ["INBOX"],
  payload: {
    headers: [
      { name: "Subject", value: "Test Email" },
      { name: "From", value: "sender@example.com" },
      { name: "To", value: "recipient@example.com" },
      { name: "Date", value: "Mon, 1 Jan 2024 00:00:00 +0000" }
    ],
    body: {
      data: btoa("This is a test email body")
    }
  },
  snippet: "This is a test email body",
  internalDate: "1704067200000"
};

describe("Gmail API Client", () => {
  let client: GmailClient;
  let fetchMock: any;
  
  beforeEach(() => {
    client = new GmailClient("mock-access-token");
    
    // fetchのモック設定（n8nのnockパターンを参考）
    fetchMock = globalThis.fetch;
    globalThis.fetch = createFetchMock();
  });
  
  afterEach(() => {
    globalThis.fetch = fetchMock;
  });

  // n8nテストケース: メッセージ一覧の取得（GmailV2.node.test.ts:373）
  it("should fetch email list", async () => {
    const options: MailFetchOptions = {
      account: "test@gmail.com",
      limit: 10
    };
    
    const emails = await client.fetchEmails(options);
    
    assertEquals(emails.length, 2);
    assertEquals(emails[0].subject, "Test Email");
    assertEquals(emails[0].fromAddress, "sender@example.com");
  });

  // n8nテストケース: クエリパラメータの構築（prepareQuery関数のテスト）
  it("should build correct query parameters", async () => {
    const testCases = [
      {
        options: { unreadOnly: true },
        expectedQuery: "is:unread"
      },
      {
        options: { since: new Date("2024-01-01") },
        expectedQuery: "after:1704067200"
      },
      {
        options: { unreadOnly: true, since: new Date("2024-01-01") },
        expectedQuery: "is:unread after:1704067200"
      }
    ];
    
    for (const testCase of testCases) {
      // fetchモックでクエリパラメータを検証
      let capturedUrl: string | null = null;
      globalThis.fetch = async (url: string | URL | Request) => {
        capturedUrl = url.toString();
        return createMockResponse(mockMessageList);
      };
      
      await client.fetchEmails({ account: "test@gmail.com", ...testCase.options });
      
      assertExists(capturedUrl);
      const url = new URL(capturedUrl);
      assertEquals(url.searchParams.get("q"), testCase.expectedQuery);
    }
  });

  // n8nテストケース: ページネーション（GmailV2.node.test.ts:390）
  it("should handle pagination", async () => {
    let callCount = 0;
    globalThis.fetch = async (url: string | URL | Request) => {
      const urlStr = url.toString();
      
      if (urlStr.includes("/messages?")) {
        callCount++;
        if (callCount === 1) {
          return createMockResponse({
            messages: [{ id: "msg1", threadId: "thread1" }],
            nextPageToken: "next-page-token"
          });
        } else {
          return createMockResponse({
            messages: [{ id: "msg2", threadId: "thread2" }]
          });
        }
      } else {
        return createMockResponse(mockMessageDetail);
      }
    };
    
    const emails = await client.fetchEmails({ account: "test@gmail.com" });
    assertEquals(emails.length, 2);
    assertEquals(callCount, 2); // 2回のリスト取得
  });

  // n8nテストケース: エラーハンドリング（APIエラーレスポンス）
  it("should handle API errors", async () => {
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({ error: { message: "Invalid credentials" } }),
        { status: 401 }
      );
    };
    
    let error: Error | null = null;
    try {
      await client.fetchEmails({ account: "test@gmail.com" });
    } catch (e) {
      error = e as Error;
    }
    
    assertExists(error);
    assert(error.message.includes("Gmail API error: 401"));
  });

  // n8nテストケース: Base64デコード（parseRawEmail関数のテスト）
  it("should decode base64 email content", async () => {
    const base64Content = "VGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keQ=="; // "This is a test email body"
    const mockMessage = {
      ...mockMessageDetail,
      payload: {
        ...mockMessageDetail.payload,
        body: { data: base64Content }
      }
    };
    
    globalThis.fetch = async (url: string | URL | Request) => {
      const urlStr = url.toString();
      if (urlStr.includes("/messages?")) {
        return createMockResponse(mockMessageList);
      } else {
        return createMockResponse(mockMessage);
      }
    };
    
    const emails = await client.fetchEmails({ account: "test@gmail.com" });
    assertEquals(emails[0].bodyText, "This is a test email body");
  });
});

// テストヘルパー関数（n8nのモックパターンを参考）
function createFetchMock() {
  return async (url: string | URL | Request): Promise<Response> => {
    const urlStr = url.toString();
    
    if (urlStr.includes("/messages?")) {
      return createMockResponse(mockMessageList);
    } else if (urlStr.includes("/messages/")) {
      return createMockResponse(mockMessageDetail);
    }
    
    return new Response("Not found", { status: 404 });
  };
}

function createMockResponse(data: any): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}