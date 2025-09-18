import * as kuzu from "kuzu-wasm";

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
}

class KuzuBrowserTest {
  private db: any;
  private conn: any;
  private results: TestResult[] = [];

  async initialize(): Promise<void> {
    console.log("🚀 Initializing KuzuDB in browser...");
    this.db = new kuzu.Database(":memory:", 1 << 28 /* 256MB */);
    this.conn = new kuzu.Connection(this.db, 4);
  }

  private addResult(name: string, passed: boolean, error?: string): void {
    this.results.push({ name, passed, error });
    const emoji = passed ? "✅" : "❌";
    console.log(`${emoji} ${name}`, error ? `- ${error}` : "");
  }

  async testSchemaOperations(): Promise<void> {
    try {
      // Create node table
      await this.conn.query(
        "CREATE NODE TABLE User(id INT64, name STRING, email STRING, PRIMARY KEY(id))"
      );
      
      // Create edge table
      await this.conn.query(
        "CREATE REL TABLE Follows(FROM User TO User, since DATE)"
      );
      
      this.addResult("Schema Operations", true);
    } catch (error) {
      this.addResult("Schema Operations", false, String(error));
    }
  }

  async testDataOperations(): Promise<void> {
    try {
      // Insert users
      const users = [
        { id: 1, name: "Alice", email: "alice@example.com" },
        { id: 2, name: "Bob", email: "bob@example.com" },
        { id: 3, name: "Charlie", email: "charlie@example.com" }
      ];

      for (const user of users) {
        await this.conn.query(
          `CREATE (:User {id: ${user.id}, name: '${user.name}', email: '${user.email}'})`
        );
      }

      // Create relationships
      await this.conn.query(
        "MATCH (a:User {id: 1}), (b:User {id: 2}) CREATE (a)-[:Follows {since: date('2023-01-15')}]->(b)"
      );
      await this.conn.query(
        "MATCH (b:User {id: 2}), (c:User {id: 3}) CREATE (b)-[:Follows {since: date('2023-06-20')}]->(c)"
      );

      // Query data
      const result = await this.conn.query("MATCH (u:User) RETURN count(*) as total");
      const rows = await result.getAllObjects();
      
      if (rows[0]["total"] === 3) {
        this.addResult("Data Operations", true);
      } else {
        this.addResult("Data Operations", false, `Expected 3 users, got ${rows[0]["total"]}`);
      }
      
      await result.close();
    } catch (error) {
      this.addResult("Data Operations", false, String(error));
    }
  }

  async testQueryOperations(): Promise<void> {
    try {
      // Complex query
      const result = await this.conn.query(`
        MATCH (u1:User)-[f:Follows]->(u2:User)
        RETURN u1.name as follower, u2.name as followed, f.since as since
        ORDER BY f.since
      `);
      
      const rows = await result.getAllObjects();
      
      if (rows.length === 2 && 
          rows[0]["follower"] === "Alice" && 
          rows[0]["followed"] === "Bob") {
        this.addResult("Query Operations", true);
      } else {
        this.addResult("Query Operations", false, "Unexpected query results");
      }
      
      await result.close();
    } catch (error) {
      this.addResult("Query Operations", false, String(error));
    }
  }

  async testAggregations(): Promise<void> {
    try {
      // Test various aggregations
      const queries = [
        "MATCH (u:User) RETURN count(*) as cnt",
        "MATCH ()-[f:Follows]->() RETURN count(*) as rel_count",
        "MATCH (u:User)-[:Follows]->() RETURN u.name, count(*) as following_count"
      ];

      for (const query of queries) {
        const result = await this.conn.query(query);
        const rows = await result.getAllObjects();
        if (rows.length === 0) {
          throw new Error(`No results for query: ${query}`);
        }
        await result.close();
      }

      this.addResult("Aggregation Operations", true);
    } catch (error) {
      this.addResult("Aggregation Operations", false, String(error));
    }
  }

  async cleanup(): Promise<void> {
    console.log("🧹 Cleaning up...");
    await this.conn.close();
    await this.db.close();
    await kuzu.close();
  }

  async runAllTests(): Promise<void> {
    await this.initialize();
    
    await this.testSchemaOperations();
    await this.testDataOperations();
    await this.testQueryOperations();
    await this.testAggregations();
    
    await this.cleanup();
    
    this.displayResults();
  }

  private displayResults(): void {
    console.log("\n📊 Test Results Summary:");
    console.log("========================");
    
    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;
    
    this.results.forEach(result => {
      const status = result.passed ? "PASS" : "FAIL";
      console.log(`  ${status}: ${result.name}`);
      if (result.error) {
        console.log(`    Error: ${result.error}`);
      }
    });
    
    console.log("------------------------");
    console.log(`Total: ${passed}/${total} tests passed`);
    
    if (passed === total) {
      console.log("🎉 All tests passed!");
    } else {
      console.log("⚠️ Some tests failed. Check the logs above.");
    }
  }
}

// Export for use in HTML
(window as any).KuzuBrowserTest = KuzuBrowserTest;