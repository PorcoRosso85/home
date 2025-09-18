/**
 * Example usage of UniversalKuzu that works in both browser and server
 */

import { UniversalKuzu } from './kuzu-universal';

async function runExample() {
  const kuzu = new UniversalKuzu();
  
  try {
    // Initialize - automatically detects environment
    console.log(`🚀 Starting KuzuDB in ${UniversalKuzu.getEnvironment()} environment`);
    await kuzu.initialize();

    // Create schema
    await kuzu.createSchema([
      "CREATE NODE TABLE Movie(title STRING, year INT64, rating DOUBLE, PRIMARY KEY(title))",
      "CREATE NODE TABLE Actor(name STRING, age INT64, PRIMARY KEY(name))",
      "CREATE REL TABLE ActsIn(FROM Actor TO Movie, role STRING)"
    ]);

    // Load data
    await kuzu.loadData([
      "CREATE (:Movie {title: 'The Matrix', year: 1999, rating: 8.7})",
      "CREATE (:Movie {title: 'Inception', year: 2010, rating: 8.8})",
      "CREATE (:Actor {name: 'Keanu Reeves', age: 59})",
      "CREATE (:Actor {name: 'Leonardo DiCaprio', age: 49})",
      "MATCH (a:Actor {name: 'Keanu Reeves'}), (m:Movie {title: 'The Matrix'}) CREATE (a)-[:ActsIn {role: 'Neo'}]->(m)",
      "MATCH (a:Actor {name: 'Leonardo DiCaprio'}), (m:Movie {title: 'Inception'}) CREATE (a)-[:ActsIn {role: 'Cobb'}]->(m)"
    ]);

    // Query data
    console.log('\n📊 Movies and their actors:');
    const results = await kuzu.queryObjects(`
      MATCH (a:Actor)-[r:ActsIn]->(m:Movie)
      RETURN a.name as actor, r.role as role, m.title as movie, m.year as year
      ORDER BY m.year DESC
    `);

    results.forEach(row => {
      console.log(`  ${row.actor} played ${row.role} in "${row.movie}" (${row.year})`);
    });

    // Aggregation query
    console.log('\n📈 Statistics:');
    const stats = await kuzu.queryOne(`
      MATCH (m:Movie)
      RETURN count(*) as totalMovies, avg(m.rating) as avgRating
    `);
    console.log(`  Total movies: ${stats.totalMovies}`);
    console.log(`  Average rating: ${stats.avgRating.toFixed(1)}`);

    // Transaction example
    console.log('\n💾 Testing transaction...');
    await kuzu.beginTransaction();
    await kuzu.query("CREATE (:Movie {title: 'Test Movie', year: 2024, rating: 0.0})");
    
    const beforeRollback = await kuzu.queryOne("MATCH (m:Movie {title: 'Test Movie'}) RETURN m.title as title");
    console.log(`  In transaction: ${beforeRollback ? 'Found "Test Movie"' : 'Not found'}`);
    
    await kuzu.rollback();
    
    const afterRollback = await kuzu.queryOne("MATCH (m:Movie {title: 'Test Movie'}) RETURN m.title as title");
    console.log(`  After rollback: ${afterRollback ? 'Found' : 'Not found (as expected)'}`);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    // Clean up
    await kuzu.cleanup();
    console.log('\n✅ Example completed!');
  }
}

// Run the example
if (import.meta.main || require.main === module) {
  runExample().catch(console.error);
}

export { runExample };