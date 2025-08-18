// Mock database connection for testing purposes
export interface DatabaseConnection {
  query(cypher: string, parameters?: Record<string, any>): QueryResultWrapper;
  close(): Promise<void>;
}

export interface QueryResult {
  records: Array<Record<string, any>>;
  summary?: {
    queryType: string;
    counters?: {
      nodesCreated?: number;
      relationshipsCreated?: number;
      propertiesSet?: number;
    };
  };
}

export interface QueryResultWrapper {
  getAll(): Promise<Array<Record<string, any>>>;
}

class MockDatabaseConnection implements DatabaseConnection {
  private isConnected: boolean = true;

  query(cypher: string, parameters?: Record<string, any>): QueryResultWrapper {
    if (!this.isConnected) {
      throw new Error('Database connection is closed');
    }

    // Handle ping queries specifically
    if (cypher.toLowerCase().includes('return "pong"') || cypher.toLowerCase().includes('ping') || cypher.toLowerCase().includes('pong')) {
      const rows = [{
        response: 'pong',
        status: 1,
        database_type: 'KuzuDB',
        health_status: 'healthy',
        message: parameters?.customMessage || 'Database connectivity test',
        statistics: parameters?.includeStats ? {
          partners: 0,
          transactions: 0,
          rewards: 0,
          rules: 0,
          total_nodes: 0
        } : null
      }];
      return {
        getAll: async () => rows
      };
    }

    // Default mock response for other queries
    const rows: Array<Record<string, any>> = [];
    return {
      getAll: async () => rows
    };
  }

  async close(): Promise<void> {
    this.isConnected = false;
  }
}

export function getConnection(): DatabaseConnection {
  return new MockDatabaseConnection();
}