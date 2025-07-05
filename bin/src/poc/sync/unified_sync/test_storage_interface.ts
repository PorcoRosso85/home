/**
 * Storage Interface Test
 * ストレージインターフェースのテスト（実装非依存）
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";

// ストレージインターフェース定義
export interface GraphStorage {
  executeTemplate(template: string, params: Record<string, any>): Promise<any>;
  getLocalState(): Promise<LocalState>;
}

// ストレージファクトリーインターフェース
export interface StorageFactory {
  createStorage(): Promise<GraphStorage>;
}

export interface LocalState {
  users: Array<{ id: string; name: string; email?: string }>;
  posts: Array<{ id: string; content: string; authorId?: string }>;
  follows: Array<{ followerId: string; targetId: string }>;
}

// ストレージ実装のテスト（実装非依存）
export async function testStorageImplementation(storage: GraphStorage) {
  // CREATE_USER テスト
  await storage.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  const state = await storage.getLocalState();
  assertEquals(state.users.length, 1);
  assertEquals(state.users[0].name, "Alice");
  
  // UPDATE_USER テスト
  await storage.executeTemplate("UPDATE_USER", {
    id: "u1",
    name: "Alice Updated"
  });
  
  const updatedState = await storage.getLocalState();
  assertEquals(updatedState.users[0].name, "Alice Updated");
  
  // CREATE_POST テスト
  await storage.executeTemplate("CREATE_POST", {
    id: "p1",
    content: "Hello World",
    authorId: "u1"
  });
  
  const postState = await storage.getLocalState();
  assertEquals(postState.posts.length, 1);
  assertEquals(postState.posts[0].content, "Hello World");
}

// インメモリ実装（テスト用）
export class InMemoryGraphStorage implements GraphStorage {
  private users = new Map<string, any>();
  private posts = new Map<string, any>();
  private follows = new Set<string>();
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<any> {
    switch (template) {
      case "CREATE_USER":
        this.users.set(params.id, { ...params });
        break;
      case "UPDATE_USER":
        const user = this.users.get(params.id);
        if (user) {
          Object.assign(user, params);
        }
        break;
      case "CREATE_POST":
        this.posts.set(params.id, { ...params });
        break;
      case "FOLLOW_USER":
        this.follows.add(`${params.followerId}->${params.targetId}`);
        break;
    }
    return { template, params, timestamp: Date.now() };
  }
  
  async getLocalState(): Promise<LocalState> {
    return {
      users: Array.from(this.users.values()),
      posts: Array.from(this.posts.values()),
      follows: Array.from(this.follows).map(f => {
        const [followerId, targetId] = f.split('->');
        return { followerId, targetId };
      })
    };
  }
}