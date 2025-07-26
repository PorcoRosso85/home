/**
 * Aggregate Cache Integration Example
 * Shows how to use AggregateCache with event processing
 */

import { AggregateCache } from "../core/cache/aggregate_cache.ts";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { TemplateEventStore } from "../event_sourcing/template_event_store.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";

/**
 * Example: Real-time dashboard with aggregate metrics
 */
export class DashboardWithAggregates {
  private client: BrowserKuzuClientImpl;
  private aggregateCache: AggregateCache;
  private eventStore: TemplateEventStore;

  constructor() {
    this.client = new BrowserKuzuClientImpl();
    this.aggregateCache = new AggregateCache();
    this.eventStore = new TemplateEventStore();
    
    this.setupAggregates();
    this.setupEventHandlers();
  }

  /**
   * Define aggregates for dashboard metrics
   */
  private setupAggregates(): void {
    // Total counts
    this.aggregateCache.defineAggregate({
      name: "total_users",
      type: "COUNT",
      target: "users"
    });

    this.aggregateCache.defineAggregate({
      name: "total_posts",
      type: "COUNT",
      target: "posts"
    });

    // Active users (with status = 'active')
    this.aggregateCache.defineAggregate({
      name: "active_users",
      type: "COUNT",
      target: "users",
      predicate: (event) => event.params.status === "active"
    });

    // Average post length
    this.aggregateCache.defineAggregate({
      name: "avg_post_length",
      type: "AVG",
      target: "posts",
      field: "content_length"
    });

    // Total engagement (likes + comments)
    this.aggregateCache.defineAggregate({
      name: "total_likes",
      type: "SUM",
      target: "likes",
      field: "count"
    });

    // Peak engagement
    this.aggregateCache.defineAggregate({
      name: "max_post_likes",
      type: "MAX",
      target: "posts",
      field: "like_count"
    });

    // Earliest user registration
    this.aggregateCache.defineAggregate({
      name: "first_user_timestamp",
      type: "MIN",
      target: "users",
      field: "created_at"
    });
  }

  /**
   * Setup event handlers to update aggregates
   */
  private setupEventHandlers(): void {
    // Process events from the client
    this.client.onRemoteEvent((event: TemplateEvent) => {
      this.processEvent(event);
    });

    // Process events from local actions
    this.eventStore.onEvent((event: TemplateEvent) => {
      this.processEvent(event);
    });
  }

  /**
   * Process an event and update aggregates
   */
  private processEvent(event: TemplateEvent): void {
    // Update aggregates based on the event
    this.aggregateCache.processEvent(event);

    // Log metrics for monitoring
    if (event.template.startsWith("CREATE_")) {
      console.log("Updated metrics after creation:", this.getMetrics());
    }
  }

  /**
   * Get current dashboard metrics
   */
  public getMetrics(): Record<string, number | null> {
    return {
      totalUsers: this.aggregateCache.getValue("total_users"),
      activeUsers: this.aggregateCache.getValue("active_users"),
      totalPosts: this.aggregateCache.getValue("total_posts"),
      avgPostLength: this.aggregateCache.getValue("avg_post_length"),
      totalLikes: this.aggregateCache.getValue("total_likes"),
      maxPostLikes: this.aggregateCache.getValue("max_post_likes"),
      firstUserTimestamp: this.aggregateCache.getValue("first_user_timestamp")
    };
  }

  /**
   * Get cache performance statistics
   */
  public getCacheStats() {
    return {
      aggregateStats: this.aggregateCache.getStats(),
      memoryStats: this.aggregateCache.getMemoryStats()
    };
  }

  /**
   * Initialize with existing events
   */
  public async initialize(): Promise<void> {
    await this.client.initialize();
    
    // Get all events and process them to build initial aggregates
    const state = await this.client.getLocalState();
    
    // Simulate events from current state
    // In a real implementation, you would replay actual events
    for (const user of state.users) {
      const event: TemplateEvent = {
        id: `init-user-${user.id}`,
        template: "CREATE_USER",
        params: { 
          id: user.id, 
          name: user.name,
          status: "active",
          created_at: Date.now() - Math.random() * 1000000000
        },
        timestamp: Date.now()
      };
      this.aggregateCache.processEvent(event);
    }

    for (const post of state.posts) {
      const event: TemplateEvent = {
        id: `init-post-${post.id}`,
        template: "CREATE_POST",
        params: { 
          id: post.id, 
          content: post.content,
          authorId: post.authorId,
          content_length: post.content.length,
          like_count: Math.floor(Math.random() * 100)
        },
        timestamp: Date.now()
      };
      this.aggregateCache.processEvent(event);
    }

    console.log("Dashboard initialized with metrics:", this.getMetrics());
  }
}

// Example usage
if (import.meta.main) {
  const dashboard = new DashboardWithAggregates();
  
  await dashboard.initialize();
  
  // Simulate some events
  const events: TemplateEvent[] = [
    {
      id: "e1",
      template: "CREATE_USER",
      params: { id: "u100", name: "New User", status: "active", created_at: Date.now() },
      timestamp: Date.now()
    },
    {
      id: "e2",
      template: "CREATE_POST",
      params: { 
        id: "p100", 
        content: "Hello, this is a new post!",
        authorId: "u100",
        content_length: 26,
        like_count: 0
      },
      timestamp: Date.now()
    },
    {
      id: "e3",
      template: "ADD_LIKES",
      params: { postId: "p100", count: 5 },
      timestamp: Date.now()
    }
  ];

  for (const event of events) {
    dashboard.processEvent(event);
  }

  console.log("\nFinal metrics:", dashboard.getMetrics());
  console.log("\nCache performance:", dashboard.getCacheStats());
}