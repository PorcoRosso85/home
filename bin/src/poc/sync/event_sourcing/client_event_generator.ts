/**
 * Client Event Generator
 * クライアント側でKuzuDB WASMの操作結果からイベントを生成
 */

export interface TemplateEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
}

export class ClientEventGenerator {
  constructor(private clientId: string) {}

  generateEvent(template: string, params: Record<string, any>): TemplateEvent {
    return {
      id: this.generateEventId(),
      template,
      params,
      timestamp: Date.now(),
      clientId: this.clientId,
      checksum: this.generateChecksum(template, params)
    };
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateChecksum(template: string, params: Record<string, any>): string {
    const data = JSON.stringify({ template, params });
    // Simple checksum for demo
    return btoa(data).slice(0, 16);
  }
}

export class MockKuzuClient {
  private events: TemplateEvent[] = [];
  private eventGenerator: ClientEventGenerator;
  private localState = new Map<string, any>();

  constructor(clientId: string) {
    this.eventGenerator = new ClientEventGenerator(clientId);
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    // Simulate local execution
    this.applyLocally(template, params);
    
    // Generate event
    const event = this.eventGenerator.generateEvent(template, params);
    this.events.push(event);
    
    return event;
  }

  private applyLocally(template: string, params: Record<string, any>): void {
    switch (template) {
      case 'CREATE_USER':
        this.localState.set(`user:${params.id}`, params);
        break;
      case 'UPDATE_USER':
        const existing = this.localState.get(`user:${params.id}`);
        if (existing) {
          this.localState.set(`user:${params.id}`, { ...existing, ...params });
        }
        break;
      case 'FOLLOW_USER':
        const followKey = `follow:${params.followerId}:${params.targetId}`;
        this.localState.set(followKey, params);
        break;
    }
  }

  getEvents(): TemplateEvent[] {
    return [...this.events];
  }

  getLocalState(): Map<string, any> {
    return new Map(this.localState);
  }
}