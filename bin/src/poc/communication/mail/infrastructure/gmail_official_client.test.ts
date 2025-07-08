/**
 * Gmail公式APIクライアントのテスト
 * TDD Red Phase: 日付フィルタリング機能
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { GmailOfficialClient } from "./gmail_official_client.ts";
import type { MailFetchOptions } from "../types.ts";

describe("GmailOfficialClient", () => {
  // TODO: 認証確認後に実装
  describe.skip("日付フィルタリング", () => {
    it("test_fetchEmails_with_since_option_filters_by_date", async () => {
      // Arrange
      const mockAuth = createMockOAuth2Client();
      const client = new GmailOfficialClient(mockAuth);
      const since = new Date("2024-01-01");
      
      const options: MailFetchOptions = {
        account: "me",
        since: since
      };
      
      // Act
      const emails = await client.fetchEmails(options);
      
      // Assert
      // すべてのメールが指定日以降であることを確認
      for (const email of emails) {
        assertEquals(
          email.receivedAt >= since,
          true,
          `Email received at ${email.receivedAt} should be after ${since}`
        );
      }
    });
    
    it("test_fetchEmails_builds_correct_query_with_since_date", async () => {
      // Arrange
      const mockAuth = createMockOAuth2Client();
      const client = new GmailOfficialClient(mockAuth);
      const since = new Date("2024-01-15T00:00:00Z");
      
      let capturedQuery: string | undefined;
      
      // Gmail APIの呼び出しをインターセプト
      mockAuth.request = async (options: any) => {
        if (options.url?.includes("/messages")) {
          const url = new URL(options.url);
          capturedQuery = url.searchParams.get("q") || undefined;
        }
        return { data: { messages: [] } };
      };
      
      const options: MailFetchOptions = {
        account: "me",
        since: since
      };
      
      // Act
      await client.fetchEmails(options);
      
      // Assert
      assertExists(capturedQuery);
      assertEquals(
        capturedQuery.includes("after:2024-01-15"),
        true,
        `Query "${capturedQuery}" should contain "after:2024-01-15"`
      );
    });
    
    it("test_fetchEmails_combines_unread_and_since_filters", async () => {
      // Arrange
      const mockAuth = createMockOAuth2Client();
      const client = new GmailOfficialClient(mockAuth);
      const since = new Date("2024-01-01");
      
      let capturedQuery: string | undefined;
      
      mockAuth.request = async (options: any) => {
        if (options.url?.includes("/messages")) {
          const url = new URL(options.url);
          capturedQuery = url.searchParams.get("q") || undefined;
        }
        return { data: { messages: [] } };
      };
      
      const options: MailFetchOptions = {
        account: "me",
        unreadOnly: true,
        since: since
      };
      
      // Act
      await client.fetchEmails(options);
      
      // Assert
      assertExists(capturedQuery);
      assertEquals(
        capturedQuery.includes("is:unread"),
        true,
        "Query should contain 'is:unread'"
      );
      assertEquals(
        capturedQuery.includes("after:2024-01-01"),
        true,
        "Query should contain 'after:2024-01-01'"
      );
    });
  });
});

/**
 * モックOAuth2Client作成
 */
function createMockOAuth2Client(): any {
  return {
    request: async (options: any) => {
      // デフォルトのモックレスポンス
      return {
        data: {
          messages: [
            { id: "msg1", threadId: "thread1" }
          ]
        }
      };
    }
  };
}