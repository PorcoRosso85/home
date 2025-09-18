// Raft-based Service Orchestrator Integration
// This module bridges Raft consensus with dynamic service orchestration

import { RaftCluster, ServiceRegistryRaft, ServiceInfo as RaftServiceInfo } from "../raft/mod.ts";
import {
  ServiceRegistry,
  ServiceEvent,
  ServiceInfo as OrchestratorServiceInfo
} from "../13.2_dynamic_service_orchestration_SELECTED/service-orchestrator.ts";

// アダプター: Orchestrator ServiceInfo を Raft ServiceInfo に変換
export function toRaftServiceInfo(service: OrchestratorServiceInfo): RaftServiceInfo {
  return {
    id: service.id,
    name: service.name,
    host: service.host,
    port: service.port,
    metadata: {
      ...service.metadata,
      healthStatus: service.healthStatus,
      deploymentType: service.deploymentType
    }
  };
}

// アダプター: Raft ServiceInfo を Orchestrator ServiceInfo に変換
export function fromRaftServiceInfo(service: RaftServiceInfo): OrchestratorServiceInfo {
  return {
    id: service.id,
    name: service.name,
    host: service.host,
    port: service.port,
    healthStatus: service.metadata?.healthStatus || "unknown",
    metadata: service.metadata || {},
    deploymentType: service.metadata?.deploymentType || "standard"
  };
}

// Raftベースのサービスレジストリ実装
export class RaftServiceRegistry implements ServiceRegistry {
  private raftRegistry: ServiceRegistryRaft;
  private eventHandlers: Map<string, (event: ServiceEvent) => void> = new Map();
  
  constructor(raftCluster: RaftCluster) {
    this.raftRegistry = new ServiceRegistryRaft(raftCluster);
  }
  
  async register(service: OrchestratorServiceInfo): Promise<void> {
    const raftService = toRaftServiceInfo(service);
    await this.raftRegistry.register(raftService);
    
    // イベントを発火
    const event: ServiceEvent = {
      type: "registered",
      service,
      timestamp: Date.now()
    };
    this.notifyHandlers(event);
  }
  
  async deregister(serviceId: string): Promise<void> {
    // Raftでは deregister が未実装なので、メタデータで無効化
    const services = await this.raftRegistry.discover("");
    const service = services.find(s => s.id === serviceId);
    
    if (service) {
      service.metadata = { ...service.metadata, deregistered: true };
      await this.raftRegistry.register(service);
      
      const event: ServiceEvent = {
        type: "deregistered",
        service: fromRaftServiceInfo(service),
        timestamp: Date.now()
      };
      this.notifyHandlers(event);
    }
  }
  
  async discover(name?: string): Promise<OrchestratorServiceInfo[]> {
    const raftServices = await this.raftRegistry.discover(name || "");
    return raftServices
      .filter(s => !s.metadata?.deregistered)
      .map(fromRaftServiceInfo);
  }
  
  async getService(id: string): Promise<OrchestratorServiceInfo | undefined> {
    const services = await this.discover();
    return services.find(s => s.id === id);
  }
  
  subscribe(handler: (event: ServiceEvent) => void): () => void {
    const id = Math.random().toString(36);
    this.eventHandlers.set(id, handler);
    return () => this.eventHandlers.delete(id);
  }
  
  private notifyHandlers(event: ServiceEvent): void {
    this.eventHandlers.forEach(handler => handler(event));
  }
  
  // イベントストリームのシミュレーション
  async *events(): AsyncGenerator<ServiceEvent> {
    // Raftクラスターの変更を監視する簡易実装
    let lastServices: string[] = [];
    
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const currentServices = await this.discover();
      const currentIds = currentServices.map(s => s.id).sort();
      const lastIds = lastServices;
      
      // 変更検出
      if (JSON.stringify(currentIds) !== JSON.stringify(lastIds)) {
        // 新規サービス検出
        for (const service of currentServices) {
          if (!lastIds.includes(service.id)) {
            yield {
              type: "registered",
              service,
              timestamp: Date.now()
            };
          }
        }
        
        lastServices = currentIds;
      }
    }
  }
}

// 高可用性オーケストレーター
export class HighAvailabilityOrchestrator {
  private raftCluster: RaftCluster;
  private registry: RaftServiceRegistry;
  
  constructor(nodeId: string, nodeAddress: string) {
    this.raftCluster = new RaftCluster();
    this.registry = new RaftServiceRegistry(this.raftCluster);
  }
  
  async join(peers: Array<{id: string, address: string}>): Promise<void> {
    // 自身をクラスターに追加
    await this.raftCluster.addNode(
      peers[0].id, 
      peers[0].address
    );
    
    // ピアを追加
    for (let i = 1; i < peers.length; i++) {
      await this.raftCluster.addNode(peers[i].id, peers[i].address);
    }
    
    // クラスター開始
    await this.raftCluster.start();
  }
  
  getRegistry(): ServiceRegistry {
    return this.registry;
  }
  
  getRaftCluster(): RaftCluster {
    return this.raftCluster;
  }
  
  async shutdown(): Promise<void> {
    await this.raftCluster.stop();
  }
}