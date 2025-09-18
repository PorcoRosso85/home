// HTTPクライアントアダプター
// bin/docs規約準拠: エラーを戻り値として扱う

import type { ServerResult, ServerError } from "../types/server.ts";

export type HttpResponse<T> = {
  status: number;
  data?: T;
  headers?: Headers;
};

export class HttpClient {
  constructor(private baseUrl: string) {}
  
  async get<T>(path: string, params?: Record<string, string>, headers?: Record<string, string>): Promise<ServerResult<HttpResponse<T>>> {
    try {
      const url = new URL(`${this.baseUrl}${path}`);
      if (params) {
        Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
      }
      
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: headers,
        signal: AbortSignal.timeout(5000)
      });
      
      const data = response.ok ? await response.json() : undefined;
      
      return {
        ok: true,
        data: {
          status: response.status,
          data,
          headers: response.headers
        }
      };
    } catch (error) {
      const serverError: ServerError = {
        code: 'HTTP_CLIENT_ERROR',
        message: error instanceof Error ? error.message : 'HTTP request failed',
        details: error
      };
      return { ok: false, error: serverError };
    }
  }
  
  async post<T>(path: string, body: unknown, headers?: Record<string, string>): Promise<ServerResult<HttpResponse<T>>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(5000)
      });
      
      const data = response.ok ? await response.json() : undefined;
      
      return {
        ok: true,
        data: {
          status: response.status,
          data,
          headers: response.headers
        }
      };
    } catch (error) {
      const serverError: ServerError = {
        code: 'HTTP_CLIENT_ERROR',
        message: error instanceof Error ? error.message : 'HTTP request failed',
        details: error
      };
      return { ok: false, error: serverError };
    }
  }
}