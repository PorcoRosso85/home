/**
 * Performance Benchmark: npm:kuzu Direct vs Worker Implementation
 * 
 * Compares:
 * - Initialization time
 * - Query execution time
 * - Memory usage
 * - Stability (panic handling)
 * 
 * Runs 100 iterations of basic operations (CREATE, INSERT, MATCH)
 */

import { Database, Connection } from "npm:kuzu";
import { 
  createDatabaseWorker, 
  createConnectionWorker,
  terminateWorker,
  WorkerDatabase,
  WorkerConnection
} from "../../core/database_worker_client.ts";

interface BenchmarkResult {
  implementation: string;
  initTime: number;
  queryTimes: {
    create: number[];
    insert: number[];
    match: number[];
  };
  memoryUsage: {
    initial: number;
    afterCreate: number;
    afterInsert: number;
    final: number;
  };
  errors: string[];
  iterations: number;
  successful: boolean;
}

interface IterationResult {
  createTime: number;
  insertTime: number;
  matchTime: number;
  error?: string;
}

/**
 * Get current memory usage in MB
 */
function getMemoryUsage(): number {
  const usage = Deno.memoryUsage();
  return Math.round((usage.heapUsed / 1024 / 1024) * 100) / 100;
}

/**
 * Run a single iteration of operations
 */
async function runIteration(
  conn: Connection | WorkerConnection,
  iteration: number
): Promise<IterationResult> {
  const result: IterationResult = {
    createTime: 0,
    insertTime: 0,
    matchTime: 0
  };

  try {
    // CREATE operation
    const createStart = performance.now();
    await conn.query(`
      CREATE (p:Person {
        id: ${iteration},
        name: 'Person${iteration}',
        age: ${20 + (iteration % 50)}
      })
    `);
    result.createTime = performance.now() - createStart;

    // INSERT operation (using MATCH + SET pattern)
    const insertStart = performance.now();
    await conn.query(`
      MATCH (p:Person {id: ${iteration}})
      SET p.email = 'person${iteration}@example.com'
    `);
    result.insertTime = performance.now() - insertStart;

    // MATCH operation
    const matchStart = performance.now();
    const matchResult = await conn.query(`
      MATCH (p:Person {id: ${iteration}})
      RETURN p.id, p.name, p.age, p.email
    `);
    const rows = await matchResult.getAll();
    result.matchTime = performance.now() - matchStart;

    // Validate result
    if (!rows || rows.length !== 1) {
      throw new Error(`Expected 1 row, got ${rows?.length || 0}`);
    }

  } catch (error) {
    result.error = error instanceof Error ? error.message : String(error);
  }

  return result;
}

/**
 * Benchmark direct npm:kuzu implementation
 */
async function benchmarkDirect(iterations: number): Promise<BenchmarkResult> {
  const result: BenchmarkResult = {
    implementation: "npm:kuzu direct",
    initTime: 0,
    queryTimes: {
      create: [],
      insert: [],
      match: []
    },
    memoryUsage: {
      initial: getMemoryUsage(),
      afterCreate: 0,
      afterInsert: 0,
      final: 0
    },
    errors: [],
    iterations: 0,
    successful: false
  };

  let db: Database | null = null;
  let conn: Connection | null = null;

  try {
    // Initialize database
    const initStart = performance.now();
    db = new Database(":memory:");
    conn = new Connection(db);
    
    // Create schema
    await conn.query(`
      CREATE NODE TABLE Person(
        id INT64, 
        name STRING, 
        age INT64, 
        email STRING, 
        PRIMARY KEY (id)
      )
    `);
    
    result.initTime = performance.now() - initStart;
    result.memoryUsage.afterCreate = getMemoryUsage();

    // Run iterations
    for (let i = 0; i < iterations; i++) {
      const iterResult = await runIteration(conn, i);
      
      if (iterResult.error) {
        result.errors.push(`Iteration ${i}: ${iterResult.error}`);
        // Stop on first error to avoid potential panics
        break;
      }
      
      result.queryTimes.create.push(iterResult.createTime);
      result.queryTimes.insert.push(iterResult.insertTime);
      result.queryTimes.match.push(iterResult.matchTime);
      result.iterations++;
    }

    result.memoryUsage.afterInsert = getMemoryUsage();
    result.successful = result.iterations === iterations;

  } catch (error) {
    result.errors.push(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
  } finally {
    // Cleanup
    try {
      if (conn) await conn.close();
      if (db) await db.close();
    } catch (cleanupError) {
      result.errors.push(`Cleanup error: ${cleanupError}`);
    }
    
    result.memoryUsage.final = getMemoryUsage();
  }

  return result;
}

/**
 * Benchmark Worker implementation
 */
async function benchmarkWorker(iterations: number): Promise<BenchmarkResult> {
  const result: BenchmarkResult = {
    implementation: "Worker-based",
    initTime: 0,
    queryTimes: {
      create: [],
      insert: [],
      match: []
    },
    memoryUsage: {
      initial: getMemoryUsage(),
      afterCreate: 0,
      afterInsert: 0,
      final: 0
    },
    errors: [],
    iterations: 0,
    successful: false
  };

  let db: WorkerDatabase | null = null;
  let conn: WorkerConnection | null = null;

  try {
    // Initialize database
    const initStart = performance.now();
    const dbResult = await createDatabaseWorker(":memory:");
    
    if (!('close' in dbResult)) {
      throw new Error(`Database creation failed: ${JSON.stringify(dbResult)}`);
    }
    
    db = dbResult as unknown as WorkerDatabase;
    const connResult = await createConnectionWorker(db);
    
    if (!('query' in connResult)) {
      throw new Error(`Connection creation failed: ${JSON.stringify(connResult)}`);
    }
    
    conn = connResult as unknown as WorkerConnection;
    
    // Create schema
    await conn.query(`
      CREATE NODE TABLE Person(
        id INT64, 
        name STRING, 
        age INT64, 
        email STRING, 
        PRIMARY KEY (id)
      )
    `);
    
    result.initTime = performance.now() - initStart;
    result.memoryUsage.afterCreate = getMemoryUsage();

    // Run iterations
    for (let i = 0; i < iterations; i++) {
      const iterResult = await runIteration(conn, i);
      
      if (iterResult.error) {
        result.errors.push(`Iteration ${i}: ${iterResult.error}`);
        // Worker should handle errors gracefully, continue
        continue;
      }
      
      result.queryTimes.create.push(iterResult.createTime);
      result.queryTimes.insert.push(iterResult.insertTime);
      result.queryTimes.match.push(iterResult.matchTime);
      result.iterations++;
    }

    result.memoryUsage.afterInsert = getMemoryUsage();
    result.successful = result.iterations === iterations;

  } catch (error) {
    result.errors.push(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
  } finally {
    // Cleanup
    try {
      if (conn) await conn.close();
      if (db) await db.close();
      terminateWorker();
    } catch (cleanupError) {
      result.errors.push(`Cleanup error: ${cleanupError}`);
    }
    
    result.memoryUsage.final = getMemoryUsage();
  }

  return result;
}

/**
 * Calculate statistics for a set of numbers
 */
function calculateStats(numbers: number[]): {
  min: number;
  max: number;
  avg: number;
  median: number;
  p95: number;
} {
  if (numbers.length === 0) {
    return { min: 0, max: 0, avg: 0, median: 0, p95: 0 };
  }

  const sorted = [...numbers].sort((a, b) => a - b);
  const sum = sorted.reduce((a, b) => a + b, 0);
  const avg = sum / sorted.length;
  const median = sorted[Math.floor(sorted.length / 2)];
  const p95Index = Math.floor(sorted.length * 0.95);
  const p95 = sorted[p95Index] || sorted[sorted.length - 1];

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    avg: Math.round(avg * 1000) / 1000,
    median: Math.round(median * 1000) / 1000,
    p95: Math.round(p95 * 1000) / 1000
  };
}

/**
 * Format benchmark results
 */
function formatResults(results: BenchmarkResult[]): string {
  let output = "# Performance Benchmark Results\n\n";
  output += `Date: ${new Date().toISOString()}\n\n`;
  
  for (const result of results) {
    output += `## ${result.implementation}\n\n`;
    
    // Summary
    output += `### Summary\n`;
    output += `- Status: ${result.successful ? "✅ Success" : "❌ Failed"}\n`;
    output += `- Iterations completed: ${result.iterations}/${result.iterations + result.errors.length}\n`;
    output += `- Initialization time: ${result.initTime.toFixed(2)}ms\n`;
    output += `- Errors: ${result.errors.length}\n\n`;
    
    // Query Performance
    output += `### Query Performance (ms)\n\n`;
    output += "| Operation | Min | Max | Avg | Median | P95 |\n";
    output += "|-----------|-----|-----|-----|--------|-----|\n";
    
    for (const [op, times] of Object.entries(result.queryTimes)) {
      const stats = calculateStats(times);
      output += `| ${op.toUpperCase()} | ${stats.min.toFixed(3)} | ${stats.max.toFixed(3)} | ${stats.avg.toFixed(3)} | ${stats.median.toFixed(3)} | ${stats.p95.toFixed(3)} |\n`;
    }
    
    // Memory Usage
    output += `\n### Memory Usage (MB)\n`;
    output += `- Initial: ${result.memoryUsage.initial}\n`;
    output += `- After schema creation: ${result.memoryUsage.afterCreate}\n`;
    output += `- After data insertion: ${result.memoryUsage.afterInsert}\n`;
    output += `- Final: ${result.memoryUsage.final}\n`;
    output += `- Total increase: ${(result.memoryUsage.final - result.memoryUsage.initial).toFixed(2)}\n\n`;
    
    // Errors
    if (result.errors.length > 0) {
      output += `### Errors\n`;
      result.errors.forEach((error, i) => {
        output += `${i + 1}. ${error}\n`;
      });
      output += "\n";
    }
  }
  
  // Comparison
  if (results.length === 2) {
    output += "## Performance Comparison\n\n";
    const [direct, worker] = results;
    
    if (direct.successful && worker.successful) {
      const directStats = {
        create: calculateStats(direct.queryTimes.create),
        insert: calculateStats(direct.queryTimes.insert),
        match: calculateStats(direct.queryTimes.match)
      };
      
      const workerStats = {
        create: calculateStats(worker.queryTimes.create),
        insert: calculateStats(worker.queryTimes.insert),
        match: calculateStats(worker.queryTimes.match)
      };
      
      output += "| Metric | Direct | Worker | Overhead |\n";
      output += "|--------|--------|--------|----------|\n";
      output += `| Init Time | ${direct.initTime.toFixed(2)}ms | ${worker.initTime.toFixed(2)}ms | ${((worker.initTime / direct.initTime - 1) * 100).toFixed(1)}% |\n`;
      output += `| CREATE Avg | ${directStats.create.avg}ms | ${workerStats.create.avg}ms | ${((workerStats.create.avg / directStats.create.avg - 1) * 100).toFixed(1)}% |\n`;
      output += `| INSERT Avg | ${directStats.insert.avg}ms | ${workerStats.insert.avg}ms | ${((workerStats.insert.avg / directStats.insert.avg - 1) * 100).toFixed(1)}% |\n`;
      output += `| MATCH Avg | ${directStats.match.avg}ms | ${workerStats.match.avg}ms | ${((workerStats.match.avg / directStats.match.avg - 1) * 100).toFixed(1)}% |\n`;
      output += `| Memory | ${(direct.memoryUsage.final - direct.memoryUsage.initial).toFixed(2)}MB | ${(worker.memoryUsage.final - worker.memoryUsage.initial).toFixed(2)}MB | ${(((worker.memoryUsage.final - worker.memoryUsage.initial) / (direct.memoryUsage.final - direct.memoryUsage.initial) - 1) * 100).toFixed(1)}% |\n`;
    }
    
    output += "\n### Stability\n";
    output += `- Direct: ${direct.successful ? "Stable" : "Unstable"} (${direct.errors.length} errors)\n`;
    output += `- Worker: ${worker.successful ? "Stable" : "Unstable"} (${worker.errors.length} errors)\n`;
  }
  
  return output;
}

/**
 * Main benchmark runner
 */
async function main() {
  console.log("Starting performance benchmark...\n");
  
  const ITERATIONS = 100;
  const results: BenchmarkResult[] = [];
  
  // Test direct implementation with panic protection
  console.log("Testing npm:kuzu direct implementation...");
  try {
    const directResult = await benchmarkDirect(ITERATIONS);
    results.push(directResult);
    console.log(`✅ Direct implementation: ${directResult.iterations}/${ITERATIONS} iterations completed`);
  } catch (error) {
    console.log(`❌ Direct implementation failed: ${error}`);
    results.push({
      implementation: "npm:kuzu direct",
      initTime: 0,
      queryTimes: { create: [], insert: [], match: [] },
      memoryUsage: { initial: 0, afterCreate: 0, afterInsert: 0, final: 0 },
      errors: [`Benchmark failed: ${error}`],
      iterations: 0,
      successful: false
    });
  }
  
  // Test Worker implementation
  console.log("\nTesting Worker implementation...");
  try {
    const workerResult = await benchmarkWorker(ITERATIONS);
    results.push(workerResult);
    console.log(`✅ Worker implementation: ${workerResult.iterations}/${ITERATIONS} iterations completed`);
  } catch (error) {
    console.log(`❌ Worker implementation failed: ${error}`);
    results.push({
      implementation: "Worker-based",
      initTime: 0,
      queryTimes: { create: [], insert: [], match: [] },
      memoryUsage: { initial: 0, afterCreate: 0, afterInsert: 0, final: 0 },
      errors: [`Benchmark failed: ${error}`],
      iterations: 0,
      successful: false
    });
  }
  
  // Output results
  const formattedResults = formatResults(results);
  console.log("\n" + formattedResults);
  
  // Save results to file
  const outputPath = new URL("./PERFORMANCE_BENCHMARK_RESULTS.md", import.meta.url).pathname;
  await Deno.writeTextFile(outputPath, formattedResults);
  console.log(`\nResults saved to: ${outputPath}`);
}

// Run benchmark
if (import.meta.main) {
  main().catch(console.error);
}