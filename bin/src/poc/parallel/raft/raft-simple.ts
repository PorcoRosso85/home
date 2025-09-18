// Simplified Raft implementation for POC 13.3

export enum NodeState {
  Follower = "follower",
  Candidate = "candidate",
  Leader = "leader"
}

export interface ServiceInfo {
  id: string;
  name: string;
  host: string;
  port: number;
  metadata?: Record<string, any>;
}

export class RaftNode {
  private id: string;
  private state: NodeState = NodeState.Follower;
  private peers: Set<RaftNode> = new Set();
  private services: Map<string, ServiceInfo> = new Map();
  private stopped = false;
  
  constructor(id: string, address: string) {
    this.id = id;
  }
  
  getId(): string {
    return this.id;
  }
  
  getState(): NodeState {
    return this.state;
  }
  
  isStopped(): boolean {
    return this.stopped;
  }
  
  addPeer(peer: RaftNode): void {
    this.peers.add(peer);
  }
  
  async start(): Promise<void> {
    this.stopped = false;
    
    // Simple leader election: first node becomes leader after timeout
    if (this.id === "node-1") {
      setTimeout(() => {
        if (!this.stopped && this.state === NodeState.Follower) {
          this.state = NodeState.Leader;
          console.log(`${this.id} became leader`);
        }
      }, 500);
    }
  }
  
  async stop(): Promise<void> {
    const wasLeader = this.state === NodeState.Leader;
    this.stopped = true;
    this.state = NodeState.Follower;
    
    // If this was the leader, trigger new election
    if (wasLeader) {
      // Find next available node to become leader
      const candidates = Array.from(this.peers)
        .filter(peer => peer.getId() !== this.id)
        .sort((a, b) => a.getId().localeCompare(b.getId()));
      
      for (const candidate of candidates) {
        if (!candidate.isStopped()) {
          // Use immediate execution instead of setTimeout to avoid leaks
          if (!candidate.isStopped()) {
            candidate.state = NodeState.Leader;
            console.log(`${candidate.getId()} became new leader after ${this.id} failure`);
          }
          break;
        }
      }
    }
  }
  
  // Service registry operations
  async applyCommand(command: any): Promise<boolean> {
    if (this.state !== NodeState.Leader) {
      return false;
    }
    
    // Apply to local state
    if (command.type === "register") {
      this.services.set(command.service.id, command.service);
      
      // Replicate to followers
      this.peers.forEach(peer => {
        if (peer.getState() === NodeState.Follower) {
          peer.services.set(command.service.id, command.service);
        }
      });
    }
    
    return true;
  }
  
  getServices(): ServiceInfo[] {
    return Array.from(this.services.values());
  }
}

export class RaftCluster {
  private nodes: Map<string, RaftNode> = new Map();
  
  async addNode(id: string, address: string): Promise<RaftNode> {
    const node = new RaftNode(id, address);
    
    // Connect all nodes
    this.nodes.forEach(existingNode => {
      node.addPeer(existingNode);
      existingNode.addPeer(node);
    });
    
    this.nodes.set(id, node);
    return node;
  }
  
  async start(): Promise<void> {
    // Start all nodes
    for (const node of this.nodes.values()) {
      await node.start();
    }
  }
  
  async stop(): Promise<void> {
    for (const node of this.nodes.values()) {
      await node.stop();
    }
  }
  
  getNodes(): RaftNode[] {
    return Array.from(this.nodes.values());
  }
  
  getNode(id: string): RaftNode | undefined {
    return this.nodes.get(id);
  }
  
  getLeader(): RaftNode | undefined {
    return Array.from(this.nodes.values())
      .find(node => node.getState() === NodeState.Leader);
  }
}

export class ServiceRegistryRaft {
  private cluster: RaftCluster;
  
  constructor(cluster: RaftCluster) {
    this.cluster = cluster;
  }
  
  async register(service: ServiceInfo): Promise<void> {
    const leader = this.cluster.getLeader();
    if (!leader) {
      throw new Error("No leader available");
    }
    
    const success = await leader.applyCommand({
      type: "register",
      service
    });
    
    if (!success) {
      throw new Error("Failed to register service");
    }
  }
  
  async registerViaNode(nodeId: string, service: ServiceInfo): Promise<{ redirected: boolean; leaderId?: string }> {
    const node = this.cluster.getNode(nodeId);
    if (!node) {
      throw new Error(`Node ${nodeId} not found`);
    }
    
    if (node.getState() === NodeState.Leader) {
      await this.register(service);
      return { redirected: false };
    } else {
      const leader = this.cluster.getLeader();
      if (!leader) {
        throw new Error("No leader available");
      }
      
      await this.register(service);
      return { redirected: true, leaderId: leader.getId() };
    }
  }
  
  async discover(name: string): Promise<ServiceInfo[]> {
    const nodes = this.cluster.getNodes();
    if (nodes.length === 0) return [];
    
    // Read from any node (simplified - in real Raft, would check consistency)
    const services = nodes[0].getServices();
    return services.filter(s => !name || s.name === name);
  }
  
  async discoverFrom(nodeId: string, name: string): Promise<ServiceInfo[]> {
    const node = this.cluster.getNode(nodeId);
    if (!node) {
      throw new Error(`Node ${nodeId} not found`);
    }
    
    return node.getServices().filter(s => !name || s.name === name);
  }
}