/**
 * Kuzu-wasm integration example for Cloudflare Workers
 * The WASM files from @kuzu/kuzu-wasm will be automatically handled by @cloudflare/vite-plugin
 */

// Import kuzu-wasm - the WASM files will be automatically processed during build
import kuzu_wasm from 'kuzu-wasm';

let kuzuInstance: any = null;
let database: any = null;
let connection: any = null;

/**
 * Initialize Kuzu database
 * This function initializes the WASM module and creates a database instance
 */
export async function initKuzu() {
  if (!kuzuInstance) {
    console.log('Initializing Kuzu WASM...');
    
    try {
      // Initialize the WASM module
      kuzuInstance = await kuzu_wasm();
      
      // Create an in-memory database
      database = await kuzuInstance.Database();
      
      // Create a connection
      connection = await kuzuInstance.Connection(database);
      
      console.log('Kuzu initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Kuzu:', error);
      throw error;
    }
  }
  
  return { kuzu: kuzuInstance, db: database, conn: connection };
}

/**
 * Example: Create a simple graph schema and add data
 */
export async function createSampleGraph() {
  const { conn } = await initKuzu();
  
  try {
    // Create node tables
    await conn.execute(`
      CREATE NODE TABLE Person(
        id INT64,
        name STRING,
        age INT64,
        PRIMARY KEY (id)
      )
    `);
    
    await conn.execute(`
      CREATE NODE TABLE City(
        id INT64,
        name STRING,
        population INT64,
        PRIMARY KEY (id)
      )
    `);
    
    // Create relationship table
    await conn.execute(`
      CREATE REL TABLE LivesIn(
        FROM Person TO City
      )
    `);
    
    // Insert sample data
    await conn.execute(`
      CREATE (p:Person {id: 1, name: 'Alice', age: 30})
    `);
    
    await conn.execute(`
      CREATE (p:Person {id: 2, name: 'Bob', age: 25})
    `);
    
    await conn.execute(`
      CREATE (c:City {id: 1, name: 'Tokyo', population: 14000000})
    `);
    
    await conn.execute(`
      CREATE (c:City {id: 2, name: 'San Francisco', population: 875000})
    `);
    
    // Create relationships
    await conn.execute(`
      MATCH (p:Person), (c:City)
      WHERE p.id = 1 AND c.id = 1
      CREATE (p)-[:LivesIn]->(c)
    `);
    
    await conn.execute(`
      MATCH (p:Person), (c:City)
      WHERE p.id = 2 AND c.id = 2
      CREATE (p)-[:LivesIn]->(c)
    `);
    
    console.log('Sample graph created successfully');
    return true;
  } catch (error) {
    console.error('Failed to create sample graph:', error);
    throw error;
  }
}

/**
 * Execute a Cypher query
 */
export async function executeQuery(query: string) {
  const { conn } = await initKuzu();
  
  try {
    const result = await conn.execute(query);
    
    // Convert result to JSON
    const resultJson = JSON.parse(result.table.toString());
    
    return {
      success: true,
      data: resultJson,
      rowCount: result.table.num_rows,
      columnCount: result.table.num_columns
    };
  } catch (error) {
    console.error('Query execution failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Example queries to demonstrate Kuzu capabilities
 */
export const sampleQueries = {
  // Find all people and their cities
  findPeopleWithCities: `
    MATCH (p:Person)-[:LivesIn]->(c:City)
    RETURN p.name AS person, p.age AS age, c.name AS city
  `,
  
  // Find people older than 25
  findOlderPeople: `
    MATCH (p:Person)
    WHERE p.age > 25
    RETURN p.name, p.age
  `,
  
  // Count people per city
  countPeoplePerCity: `
    MATCH (p:Person)-[:LivesIn]->(c:City)
    RETURN c.name AS city, COUNT(p) AS person_count
  `,
  
  // Get all nodes
  getAllNodes: `
    MATCH (n)
    RETURN n.*
  `
};

/**
 * Helper function to test if Kuzu is working
 */
export async function testKuzu() {
  try {
    console.log('Testing Kuzu integration...');
    
    // Initialize
    await initKuzu();
    
    // Create sample data
    await createSampleGraph();
    
    // Run a test query
    const result = await executeQuery(sampleQueries.findPeopleWithCities);
    
    console.log('Test query result:', result);
    
    return {
      success: true,
      message: 'Kuzu is working correctly!',
      result
    };
  } catch (error) {
    console.error('Kuzu test failed:', error);
    return {
      success: false,
      message: 'Kuzu test failed',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}