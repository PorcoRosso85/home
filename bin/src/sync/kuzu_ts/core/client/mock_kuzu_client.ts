/**
 * Mock KuzuDB Client for Testing
 * テスト用のモックKuzuDBクライアント
 */

import type { BrowserKuzuClient, LocalState, EventSnapshot } from "../../types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";
import { createTemplateEvent } from "../../event_sourcing/core.ts";

type MockDatabase = {
  users: Map<string, { id: string; name: string; email?: string }>;
  posts: Map<string, { id: string; content: string; authorId: string }>;
  follows: Set<string>; // "followerId:targetId"
  queries: string[]; // Track executed queries
};

export class MockKuzuClient implements BrowserKuzuClient {
  private db: MockDatabase = {
    users: new Map(),
    posts: new Map(),
    follows: new Set(),
    queries: []
  };
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private clientId = `mock_${crypto.randomUUID()}`;
  private static conflictCounter = 0;
  private static conflictTargetId?: string;

  async initialize(): Promise<void> {
    // No-op for mock
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    this.events = [...snapshot.events];
    for (const event of snapshot.events) {
      await this.applyEvent(event);
    }
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    const event = createTemplateEvent(template, params, this.clientId);
    await this.applyEvent(event);
    this.events.push(event);
    return event;
  }

  async getLocalState(): Promise<LocalState> {
    return {
      users: Array.from(this.db.users.values()),
      posts: Array.from(this.db.posts.values()),
      follows: Array.from(this.db.follows).map(f => {
        const [followerId, targetId] = f.split(':');
        return { followerId, targetId };
      })
    };
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    // Track the query
    this.db.queries.push(cypher);

    // Mock transaction commands
    if (cypher === "BEGIN TRANSACTION") {
      return { success: true };
    }
    if (cypher === "COMMIT") {
      return { success: true };
    }
    if (cypher === "ROLLBACK") {
      return { success: true };
    }

    // Mock query results
    if (cypher.includes("CREATE") && cypher.includes("User")) {
      if (params) {
        this.db.users.set(params.id, {
          id: params.id,
          name: params.name,
          email: params.email
        });
      }
      return { success: true };
    }

    if (cypher.includes("MATCH") && cypher.includes("User")) {
      if (params?.id) {
        const user = this.db.users.get(params.id);
        return {
          getAllObjects: () => user ? [{ name: user.name, email: user.email }] : []
        };
      }
    }

    return { success: true };
  }

  private async applyEvent(event: TemplateEvent): Promise<void> {
    switch (event.template) {
      case 'CREATE_USER':
        this.db.users.set(event.params.id, {
          id: event.params.id,
          name: event.params.name,
          email: event.params.email
        });
        break;
      case 'UPDATE_USER':
        // Simulate serialization conflict for specific test
        if (event.params.id === "user-conflict") {
          if (!MockKuzuClient.conflictTargetId) {
            MockKuzuClient.conflictTargetId = event.params.id;
            MockKuzuClient.conflictCounter = 0;
          }
          
          MockKuzuClient.conflictCounter++;
          
          // First update succeeds, second one fails
          if (MockKuzuClient.conflictCounter > 1) {
            throw new Error("Serialization conflict: concurrent update");
          }
        }
        
        const user = this.db.users.get(event.params.id);
        if (user) {
          user.name = event.params.name;
        }
        break;
      case 'CREATE_POST':
        this.db.posts.set(event.params.id, {
          id: event.params.id,
          content: event.params.content,
          authorId: event.params.authorId
        });
        break;
      case 'FOLLOW_USER':
        this.db.follows.add(`${event.params.followerId}:${event.params.targetId}`);
        break;
    }

    // Notify handlers
    this.remoteEventHandlers.forEach(handler => handler(event));
  }

  // Test helpers
  getExecutedQueries(): string[] {
    return this.db.queries;
  }

  clearQueries(): void {
    this.db.queries = [];
  }
}