/**
 * Gmail API クライアント実装
 * 
 * @module mail/infrastructure/gmail_client
 * @description Gmail APIとの通信を担当するアダプター
 * 
 * 参考実装:
 * - n8n: packages/nodes-base/nodes/Google/Gmail/v2/GmailV2.node.ts
 * - n8n: packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts
 */

import type { Email, MailFetchOptions } from "../types.ts";

// Gmail APIのレスポンス型
interface GmailMessage {
  id: string;
  threadId: string;
  labelIds?: string[];
  snippet?: string;
  payload?: {
    headers?: Array<{ name: string; value: string }>;
    body?: { data?: string };
    parts?: Array<{ 
      mimeType?: string;
      body?: { data?: string };
    }>;
  };
  internalDate?: string;
}

interface GmailListResponse {
  messages: Array<{ id: string; threadId: string }>;
  nextPageToken?: string;
  resultSizeEstimate?: number;
}

/**
 * Gmail APIクライアント
 */
/**
 * Gmail APIクライアント
 * 
 * @example
 * ```typescript
 * const client = new GmailClient("access-token");
 * const emails = await client.fetchEmails({ unreadOnly: true });
 * ```
 */
export class GmailClient {
  // 借用元: GenericFunctions.ts内のgoogleApiRequest関数で使用されるbaseURL
  private baseUrl = "https://www.googleapis.com/gmail/v1";
  
  constructor(private accessToken: string) {}
  
  /**
   * メール一覧を取得
   * 
   * @param options - 取得オプション
   * @returns メールの配列
   */
  async fetchEmails(options: MailFetchOptions): Promise<Email[]> {
    const emails: Email[] = [];
    let nextPageToken: string | undefined;
    
    do {
      // クエリパラメータの構築
      // 借用元概念: GmailV2.node.ts:376-378 (prepareQuery関数)
      const params = this.buildQueryParams(options, nextPageToken);
      
      // メッセージ一覧を取得
      // 借用元: GmailV2.node.ts:391-397 (googleApiRequest呼び出し)
      const listResponse = await this.apiRequest<GmailListResponse>(
        "GET",
        `/users/me/messages?${params}`
      );
      
      if (!listResponse.messages || listResponse.messages.length === 0) {
        break;
      }
      
      // 各メッセージの詳細を取得
      for (const message of listResponse.messages) {
        const detail = await this.fetchMessageDetail(message.id);
        if (detail) {
          emails.push(detail);
        }
        
        // 制限に達したら終了
        if (options.limit && emails.length >= options.limit) {
          return emails.slice(0, options.limit);
        }
      }
      
      nextPageToken = listResponse.nextPageToken;
    } while (nextPageToken && (!options.limit || emails.length < options.limit));
    
    return emails;
  }
  
  /**
   * メッセージの詳細を取得
   * 借用元: GmailV2.node.ts:415-421 (各メッセージの詳細取得)
   */
  private async fetchMessageDetail(messageId: string): Promise<Email | null> {
    try {
      // 借用元: GmailV2.node.ts:351 (format=rawの代わりにfullを使用)
      const message = await this.apiRequest<GmailMessage>(
        "GET",
        `/users/me/messages/${messageId}?format=full`
      );
      
      return this.convertToEmail(message);
    } catch (error) {
      console.error(`Failed to fetch message ${messageId}:`, error);
      return null;
    }
  }
  
  /**
   * GmailメッセージをEmail型に変換
   * 借用元概念: GenericFunctions.tsのsimplifyOutput関数
   */
  private convertToEmail(message: GmailMessage): Email {
    const headers = this.extractHeaders(message);
    const body = this.extractBody(message);
    
    return {
      id: message.id,
      accountId: "gmail", // 仮の値
      messageId: message.id,
      subject: headers.subject || "(no subject)",
      fromAddress: headers.from || "",
      toAddresses: this.parseAddresses(headers.to),
      ccAddresses: headers.cc ? this.parseAddresses(headers.cc) : undefined,
      bodyText: body.text,
      bodyHtml: body.html,
      headers: headers,
      isRead: !message.labelIds?.includes("UNREAD"),
      receivedAt: new Date(parseInt(message.internalDate || "0")),
    };
  }
  
  /**
   * ヘッダー情報を抽出
   */
  private extractHeaders(message: GmailMessage): Record<string, string> {
    const headers: Record<string, string> = {};
    
    if (message.payload?.headers) {
      for (const header of message.payload.headers) {
        headers[header.name.toLowerCase()] = header.value;
      }
    }
    
    return headers;
  }
  
  /**
   * メール本文を抽出
   */
  private extractBody(message: GmailMessage): { text?: string; html?: string } {
    const body: { text?: string; html?: string } = {};
    
    // シンプルなメッセージ
    if (message.payload?.body?.data) {
      body.text = this.decodeBase64(message.payload.body.data);
      return body;
    }
    
    // マルチパートメッセージ
    if (message.payload?.parts) {
      for (const part of message.payload.parts) {
        if (part.body?.data) {
          const decoded = this.decodeBase64(part.body.data);
          if (part.mimeType === "text/plain") {
            body.text = decoded;
          } else if (part.mimeType === "text/html") {
            body.html = decoded;
          }
        }
      }
    }
    
    return body;
  }
  
  /**
   * クエリパラメータを構築
   * 借用元: GenericFunctions.tsのprepareQuery関数
   */
  private buildQueryParams(options: MailFetchOptions, pageToken?: string): string {
    const params = new URLSearchParams();
    
    // クエリ条件
    const query: string[] = [];
    
    // 借用元: prepareQuery内でのreadStatus処理
    if (options.unreadOnly) {
      query.push("is:unread");
    }
    
    // 借用元: prepareQuery内でのreceivedAfter処理
    if (options.since) {
      const timestamp = Math.floor(options.since.getTime() / 1000);
      query.push(`after:${timestamp}`);
    }
    
    if (query.length > 0) {
      params.set("q", query.join(" "));
    }
    
    // ページネーション
    if (pageToken) {
      params.set("pageToken", pageToken);
    }
    
    // 1ページあたりの最大件数
    // 借用元: GmailV2.node.ts:390 (maxResultsの設定)
    const maxResults = options.limit && options.limit < 100 ? options.limit : 100;
    params.set("maxResults", maxResults.toString());
    
    return params.toString();
  }
  
  /**
   * APIリクエストを実行
   * 借用元概念: GenericFunctions.tsのgoogleApiRequest関数
   */
  private async apiRequest<T>(method: string, endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: {
        "Authorization": `Bearer ${this.accessToken}`,
        "Accept": "application/json",
      },
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Gmail API error: ${response.status} ${error}`);
    }
    
    return response.json();
  }
  
  /**
   * Base64デコード
   * 借用元: GenericFunctions.tsのparseRawEmail関数内の処理
   */
  private decodeBase64(data: string): string {
    // URLセーフなBase64をデコード
    const base64 = data.replace(/-/g, "+").replace(/_/g, "/");
    return atob(base64);
  }
  
  /**
   * アドレス文字列をパース
   */
  private parseAddresses(addressStr: string): string[] {
    return addressStr
      .split(",")
      .map(addr => addr.trim())
      .filter(addr => addr.length > 0);
  }
}