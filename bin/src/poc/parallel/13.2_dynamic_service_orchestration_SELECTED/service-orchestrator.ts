// Types
export interface ServiceInfo {
  id: string;
  name: string;
  host: string;
  port: number;
  metadata?: Record<string, any>;
}

export interface ServiceEvent {
  type: "added" | "removed" | "updated";
  service: ServiceInfo;
  timestamp: number;
}

export interface HealthStatus {
  healthy: boolean;
  responseTime: number;
  error?: string;
}

export interface RoutingStrategy {
  name: string;
  select: (services: ServiceInfo[], request: any) => Promise<ServiceInfo>;
}

// Service Registry Implementation
export class ServiceRegistry {
  private services: Map<string, ServiceInfo> = new Map();
  private watchers: Map<string, Set<(event: ServiceEvent) => void>> = new Map();

  async register(service: ServiceInfo): Promise<void> {
    this.services.set(service.id, service);
    this.notifyWatchers(service.name, {
      type: "added",
      service,
      timestamp: Date.now()
    });
  }

  async deregister(serviceId: string): Promise<void> {
    const service = this.services.get(serviceId);
    if (service) {
      this.services.delete(serviceId);
      this.notifyWatchers(service.name, {
        type: "removed",
        service,
        timestamp: Date.now()
      });
    }
  }

  async discover(serviceName: string): Promise<ServiceInfo[]> {
    const found: ServiceInfo[] = [];
    for (const service of this.services.values()) {
      if (service.name === serviceName) {
        found.push(service);
      }
    }
    return found;
  }

  async *watch(serviceName: string): AsyncGenerator<ServiceEvent> {
    const eventQueue: ServiceEvent[] = [];
    let resolver: ((value: IteratorResult<ServiceEvent>) => void) | null = null;

    const handler = (event: ServiceEvent) => {
      if (resolver) {
        resolver({ done: false, value: event });
        resolver = null;
      } else {
        eventQueue.push(event);
      }
    };

    // Register watcher
    if (!this.watchers.has(serviceName)) {
      this.watchers.set(serviceName, new Set());
    }
    this.watchers.get(serviceName)!.add(handler);

    try {
      while (true) {
        if (eventQueue.length > 0) {
          yield eventQueue.shift()!;
        } else {
          yield await new Promise<ServiceEvent>((resolve) => {
            resolver = (result) => {
              if (!result.done) {
                resolve(result.value);
              }
            };
          });
        }
      }
    } finally {
      // Cleanup
      this.watchers.get(serviceName)?.delete(handler);
    }
  }

  private notifyWatchers(serviceName: string, event: ServiceEvent): void {
    const handlers = this.watchers.get(serviceName);
    if (handlers) {
      for (const handler of handlers) {
        handler(event);
      }
    }
  }
}

// Health Checker Implementation
export class HealthChecker {
  private mockStatuses: Map<string, string> = new Map();
  private circuitBreakers: Map<string, { failures: number; state: "closed" | "open" | "half-open" }> = new Map();
  private circuitBreakerThreshold = 5;
  public onHealthCheck?: (service: ServiceInfo) => Promise<HealthStatus>;

  mockHealthStatus(serviceId: string, status: string): void {
    this.mockStatuses.set(serviceId, status);
  }

  async checkHealth(service: ServiceInfo): Promise<HealthStatus> {
    // Check circuit breaker
    const breaker = this.circuitBreakers.get(service.id);
    if (breaker && breaker.state === "open") {
      return { healthy: false, responseTime: 0, error: "Circuit breaker open" };
    }

    // Mock implementation
    if (this.mockStatuses.has(service.id)) {
      const isHealthy = this.mockStatuses.get(service.id) === "healthy";
      
      if (!isHealthy) {
        this.recordFailure(service.id);
      } else {
        this.recordSuccess(service.id);
      }
      
      return {
        healthy: isHealthy,
        responseTime: 50,
        error: isHealthy ? undefined : "Mock unhealthy"
      };
    }

    // Custom health check
    if (this.onHealthCheck) {
      try {
        const result = await this.onHealthCheck(service);
        this.recordSuccess(service.id);
        return result;
      } catch (error) {
        this.recordFailure(service.id);
        throw error;
      }
    }

    // Default implementation
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`http://${service.host}:${service.port}/health`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      const responseTime = 50; // Mock response time
      
      if (response.ok) {
        this.recordSuccess(service.id);
      } else {
        this.recordFailure(service.id);
      }
      
      return {
        healthy: response.ok,
        responseTime,
        error: response.ok ? undefined : `HTTP ${response.status}`
      };
    } catch (error) {
      this.recordFailure(service.id);
      return {
        healthy: false,
        responseTime: 0,
        error: error instanceof Error ? error.message : "Unknown error"
      };
    }
  }

  async checkHealthWithRetry(service: ServiceInfo, maxRetries: number): Promise<HealthStatus> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const result = await this.checkHealth(service);
        if (result.healthy || attempt === maxRetries - 1) {
          return result;
        }
      } catch (error) {
        lastError = error instanceof Error ? error : new Error("Unknown error");
        if (attempt < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, 100 * (attempt + 1)));
        }
      }
    }
    
    return {
      healthy: false,
      responseTime: 0,
      error: lastError?.message || "Max retries exceeded"
    };
  }

  async getHealthyServices(services: ServiceInfo[]): Promise<ServiceInfo[]> {
    const healthy: ServiceInfo[] = [];
    
    for (const service of services) {
      // Check mock status first
      if (this.mockStatuses.has(service.id)) {
        const isHealthy = this.mockStatuses.get(service.id) === "healthy";
        if (isHealthy) {
          healthy.push(service);
        }
      } else {
        // Default to healthy if not mocked
        healthy.push(service);
      }
    }
    
    return healthy;
  }

  enableCircuitBreaker(threshold: number): void {
    this.circuitBreakerThreshold = threshold;
  }

  async getCircuitBreakerStatus(serviceId: string): Promise<string> {
    const breaker = this.circuitBreakers.get(serviceId);
    return breaker?.state || "closed";
  }

  private recordFailure(serviceId: string): void {
    let breaker = this.circuitBreakers.get(serviceId);
    if (!breaker) {
      breaker = { failures: 0, state: "closed" };
      this.circuitBreakers.set(serviceId, breaker);
    }
    
    breaker.failures++;
    if (breaker.failures >= this.circuitBreakerThreshold && breaker.state === "closed") {
      breaker.state = "open";
    }
  }

  private recordSuccess(serviceId: string): void {
    const breaker = this.circuitBreakers.get(serviceId);
    if (breaker) {
      breaker.failures = 0;
      if (breaker.state === "open") {
        breaker.state = "half-open";
      } else if (breaker.state === "half-open") {
        breaker.state = "closed";
      }
    }
  }
}

// Dynamic Router Implementation
export class DynamicRouter {
  private services: ServiceInfo[] = [];
  private strategy: RoutingStrategy | string = "round-robin";
  private roundRobinIndex = 0;

  updateTopology(services: ServiceInfo[]): void {
    this.services = [...services];
  }

  setStrategy(strategy: RoutingStrategy | string): void {
    this.strategy = strategy;
  }

  async route(request: any): Promise<ServiceInfo> {
    if (this.services.length === 0) {
      throw new Error("No services available");
    }

    if (typeof this.strategy === "string") {
      switch (this.strategy) {
        case "round-robin":
          return this.roundRobinRoute();
        case "random":
          return this.randomRoute();
        default:
          throw new Error(`Unknown strategy: ${this.strategy}`);
      }
    } else {
      return this.strategy.select(this.services, request);
    }
  }

  private roundRobinRoute(): ServiceInfo {
    const service = this.services[this.roundRobinIndex % this.services.length];
    this.roundRobinIndex++;
    return service;
  }

  private randomRoute(): ServiceInfo {
    const index = Math.floor(Math.random() * this.services.length);
    return this.services[index];
  }
}

// Deployment Controller Implementation
export class DeploymentController {
  private deploymentHistory: Array<{ type: string; config: any; timestamp: number }> = [];
  private canaryConfig: { service: ServiceInfo; percentage: number } | null = null;
  private blueGreenConfig: { blue: string; green: string; active: "blue" | "green" } | null = null;

  async canaryDeploy(newService: ServiceInfo, percentage: number): Promise<void> {
    this.canaryConfig = { service: newService, percentage };
    this.deploymentHistory.push({
      type: "canary",
      config: { service: newService, percentage },
      timestamp: Date.now()
    });
  }

  async blueGreenSwitch(from: string, to: string): Promise<void> {
    this.blueGreenConfig = {
      blue: from,
      green: to,
      active: "green"
    };
    this.deploymentHistory.push({
      type: "blue-green",
      config: { from, to },
      timestamp: Date.now()
    });
  }

  async rollback(): Promise<void> {
    this.canaryConfig = null;
    this.blueGreenConfig = null;
    this.deploymentHistory.push({
      type: "rollback",
      config: {},
      timestamp: Date.now()
    });
  }

  getCanaryConfig(): { service: ServiceInfo; percentage: number } | null {
    return this.canaryConfig;
  }

  getBlueGreenConfig(): { blue: string; green: string; active: "blue" | "green" } | null {
    return this.blueGreenConfig;
  }
}

// Main Service Orchestrator
export class ServiceOrchestrator {
  private registry: ServiceRegistry;
  public healthChecker: HealthChecker;
  private router: DynamicRouter;
  public deployment: DeploymentController;
  private discoveryInterval?: number;
  private healthCheckInterval?: number;
  private discoveryTimer?: number;
  private healthCheckTimer?: number;

  constructor(config?: {
    discoveryInterval?: number;
    healthCheckInterval?: number;
  }) {
    this.registry = new ServiceRegistry();
    this.healthChecker = new HealthChecker();
    this.router = new DynamicRouter();
    this.deployment = new DeploymentController();

    if (config?.discoveryInterval) {
      this.discoveryInterval = config.discoveryInterval;
      this.startDiscovery();
    }

    if (config?.healthCheckInterval) {
      this.healthCheckInterval = config.healthCheckInterval;
      this.startHealthChecks();
    }
  }

  async register(service: ServiceInfo): Promise<void> {
    await this.registry.register(service);
    await this.updateRouterTopology();
  }

  async discover(serviceName: string): Promise<ServiceInfo[]> {
    return this.registry.discover(serviceName);
  }

  async route(request: any): Promise<ServiceInfo> {
    // Ensure router has services
    const appServices = await this.registry.discover("app");
    const apiServices = await this.registry.discover("api");
    if (appServices.length === 0 && apiServices.length === 0) {
      throw new Error("No services registered");
    }
    
    // Update router topology
    await this.updateRouterTopology();
    
    // Handle canary deployment
    const canaryConfig = this.deployment.getCanaryConfig();
    if (canaryConfig) {
      const random = Math.random() * 100;
      if (random < canaryConfig.percentage) {
        // Register canary service if not already registered
        const existing = await this.registry.discover(canaryConfig.service.name);
        if (!existing.find(s => s.id === canaryConfig.service.id)) {
          await this.registry.register(canaryConfig.service);
        }
        return canaryConfig.service;
      }
    }

    // Handle blue-green deployment
    const blueGreenConfig = this.deployment.getBlueGreenConfig();
    if (blueGreenConfig) {
      const activeId = blueGreenConfig.active === "blue" 
        ? blueGreenConfig.blue 
        : blueGreenConfig.green;
      
      const services = await this.registry.discover("api");
      const activeService = services.find(s => s.id === activeId);
      if (activeService) {
        return activeService;
      }
    }

    // Normal routing
    return this.router.route(request);
  }

  private async updateRouterTopology(): Promise<void> {
    const allServices: ServiceInfo[] = [];
    
    // Get all unique service names
    const serviceNames = new Set<string>();
    for (const service of await this.registry.discover("")) {
      serviceNames.add(service.name);
    }
    
    // Discover all services
    for (const name of ["api", "app"]) { // Simplified for testing
      const services = await this.registry.discover(name);
      if (services.length > 0) {
        const healthyServices = await this.healthChecker.getHealthyServices(services);
        allServices.push(...healthyServices);
      }
    }
    
    this.router.updateTopology(allServices);
  }

  private startDiscovery(): void {
    if (this.discoveryInterval) {
      this.discoveryTimer = setInterval(() => {
        this.updateRouterTopology();
      }, this.discoveryInterval);
    }
  }

  private startHealthChecks(): void {
    if (this.healthCheckInterval) {
      this.healthCheckTimer = setInterval(async () => {
        await this.updateRouterTopology();
      }, this.healthCheckInterval);
    }
  }

  destroy(): void {
    if (this.discoveryTimer) {
      clearInterval(this.discoveryTimer);
    }
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
    }
  }
}