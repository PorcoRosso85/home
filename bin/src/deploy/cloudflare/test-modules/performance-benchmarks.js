/**
 * Performance Benchmarks and Validation Tests
 *
 * Tests performance characteristics of the R2 connection management system
 * including execution speed, memory usage, caching efficiency, and scalability.
 * Provides benchmarks for optimization and regression detection.
 *
 * Test scenarios:
 * - Command execution performance
 * - Memory usage analysis
 * - Cache performance optimization
 * - Concurrent operation handling
 * - Resource usage monitoring
 * - Scalability testing
 * - Performance regression detection
 */

const fs = require('fs');
const path = require('path');

/**
 * Run performance benchmark tests
 */
async function runTests(testSuite) {
  const { logger } = testSuite;

  logger.info('Running Performance Benchmarks and Validation Tests...');

  // Test 1: Command Execution Performance
  await testSuite.runTest('Command Execution Performance', async () => {
    await testCommandExecutionPerformance(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 2: Memory Usage Analysis
  await testSuite.runTest('Memory Usage Analysis', async () => {
    await testMemoryUsageAnalysis(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 3: Cache Performance Optimization
  await testSuite.runTest('Cache Performance Optimization', async () => {
    await testCachePerformanceOptimization(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 4: Concurrent Operation Handling
  await testSuite.runTest('Concurrent Operation Handling', async () => {
    await testConcurrentOperationHandling(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 5: Resource Usage Monitoring
  await testSuite.runTest('Resource Usage Monitoring', async () => {
    await testResourceUsageMonitoring(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 6: Scalability Testing
  await testSuite.runTest('Scalability Testing', async () => {
    await testScalabilityTesting(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 7: I/O Performance Analysis
  await testSuite.runTest('I/O Performance Analysis', async () => {
    await testIOPerformanceAnalysis(testSuite);
  }, { category: 'PERFORMANCE' });

  // Test 8: Performance Regression Detection
  await testSuite.runTest('Performance Regression Detection', async () => {
    await testPerformanceRegressionDetection(testSuite);
  }, { category: 'PERFORMANCE' });
}

/**
 * Test command execution performance
 */
async function testCommandExecutionPerformance(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing command execution performance...');

  const commands = [
    { name: 'just --version', category: 'basic' },
    { name: 'just --list', category: 'basic' },
    { name: 'nix run .#status', category: 'complex' },
    { name: 'nix run .#r2:envs', category: 'complex' },
    { name: 'nix run .#r2 -- status dev', category: 'complex' },
    { name: 'nix run .#secrets -- check', category: 'complex' }
  ];

  const performanceResults = [];

  for (const command of commands) {
    const iterations = command.category === 'basic' ? 10 : 5;
    const times = [];

    logger.debug(`Benchmarking: ${command.name} (${iterations} iterations)`);

    for (let i = 0; i < iterations; i++) {
      try {
        const startTime = process.hrtime.bigint();

        const result = await testSuite.execCommand(command.name, { timeout: 30000 });

        const endTime = process.hrtime.bigint();
        const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds

        if (result.code === 0) {
          times.push(duration);
        } else {
          logger.debug(`Command failed on iteration ${i + 1}: ${command.name}`);
        }

      } catch (error) {
        logger.debug(`Command error on iteration ${i + 1}: ${command.name} - ${error.message}`);
      }
    }

    if (times.length > 0) {
      const stats = calculatePerformanceStats(times);
      performanceResults.push({
        command: command.name,
        category: command.category,
        iterations: times.length,
        ...stats
      });

      logger.performance(`${command.name}: avg=${stats.average.toFixed(2)}ms, min=${stats.min.toFixed(2)}ms, max=${stats.max.toFixed(2)}ms`);
    }
  }

  // Analyze results
  const basicCommands = performanceResults.filter(r => r.category === 'basic');
  const complexCommands = performanceResults.filter(r => r.category === 'complex');

  if (basicCommands.length > 0) {
    const avgBasic = basicCommands.reduce((sum, r) => sum + r.average, 0) / basicCommands.length;
    logger.performance(`Basic commands average: ${avgBasic.toFixed(2)}ms`);

    if (avgBasic > 1000) {
      logger.warn('Basic commands are slower than expected (>1s)');
    }
  }

  if (complexCommands.length > 0) {
    const avgComplex = complexCommands.reduce((sum, r) => sum + r.average, 0) / complexCommands.length;
    logger.performance(`Complex commands average: ${avgComplex.toFixed(2)}ms`);

    if (avgComplex > 10000) {
      logger.warn('Complex commands are slower than expected (>10s)');
    }
  }

  // Test cold vs warm start performance
  logger.debug('Testing cold vs warm start performance...');

  const testCommand = 'nix run .#r2 -- status dev';

  // Cold start (first execution)
  const coldStart = await measureExecutionTime(() =>
    testSuite.execCommand(testCommand, { timeout: 30000 })
  );

  // Warm start (second execution)
  const warmStart = await measureExecutionTime(() =>
    testSuite.execCommand(testCommand, { timeout: 30000 })
  );

  if (coldStart.success && warmStart.success) {
    const improvement = ((coldStart.duration - warmStart.duration) / coldStart.duration) * 100;
    logger.performance(`Cold start: ${coldStart.duration.toFixed(2)}ms, Warm start: ${warmStart.duration.toFixed(2)}ms`);
    logger.performance(`Warm start improvement: ${improvement.toFixed(1)}%`);

    if (improvement < 0) {
      logger.warn('Warm start is slower than cold start - investigate caching issues');
    }
  }

  logger.debug('Command execution performance analysis completed');
}

/**
 * Test memory usage analysis
 */
async function testMemoryUsageAnalysis(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing memory usage analysis...');

  const baseline = process.memoryUsage();
  logger.performance(`Baseline memory: ${formatMemoryUsage(baseline)}`);

  // Test memory usage with SOPS helper
  const sopsHelper = require('../helpers/sops-yaml.js');

  // Clear cache and measure
  sopsHelper.clearCache();
  const afterClear = process.memoryUsage();

  // Load configurations
  const memoryTests = [
    { name: 'Single config load', action: () => sopsHelper.getEnvironmentConfig('r2', 'dev', true) },
    { name: 'Multiple environment load', action: async () => {
      await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
      await sopsHelper.getEnvironmentConfig('r2', 'stg', true);
      await sopsHelper.getEnvironmentConfig('r2', 'prod', true);
    }},
    { name: 'Repeated loads (cache test)', action: async () => {
      for (let i = 0; i < 10; i++) {
        await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
      }
    }},
    { name: 'Cache statistics', action: () => sopsHelper.getCacheStats() }
  ];

  const memoryResults = [];

  for (const test of memoryTests) {
    const beforeMemory = process.memoryUsage();

    try {
      await test.action();

      const afterMemory = process.memoryUsage();
      const delta = {
        rss: afterMemory.rss - beforeMemory.rss,
        heapUsed: afterMemory.heapUsed - beforeMemory.heapUsed,
        heapTotal: afterMemory.heapTotal - beforeMemory.heapTotal,
        external: afterMemory.external - beforeMemory.external
      };

      memoryResults.push({
        test: test.name,
        delta: delta,
        afterMemory: afterMemory
      });

      logger.performance(`${test.name}: ${formatMemoryDelta(delta)}`);

    } catch (error) {
      logger.debug(`Memory test error: ${test.name} - ${error.message}`);
    }
  }

  // Test memory leaks
  logger.debug('Testing for memory leaks...');

  const initialMemory = process.memoryUsage();

  for (let cycle = 0; cycle < 5; cycle++) {
    // Perform operations that might leak memory
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    await sopsHelper.getEnvironmentConfig('r2', 'stg', true);
    await sopsHelper.getEnvironmentConfig('r2', 'prod', true);

    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }

    const currentMemory = process.memoryUsage();
    const leakDelta = currentMemory.heapUsed - initialMemory.heapUsed;

    logger.performance(`Leak test cycle ${cycle + 1}: heap delta ${(leakDelta / 1024 / 1024).toFixed(2)}MB`);

    if (leakDelta > 50 * 1024 * 1024) { // 50MB
      logger.warn(`Potential memory leak detected after cycle ${cycle + 1}`);
    }
  }

  // Test large data handling
  logger.debug('Testing large data handling...');

  const largeConfig = {
    cf_account_id: '1234567890abcdef1234567890abcdef',
    r2_buckets: Array(1000).fill().map((_, i) => `bucket-${i}`),
    large_data: 'x'.repeat(100000) // 100KB string
  };

  const beforeLarge = process.memoryUsage();

  try {
    // Simulate processing large configuration
    const processed = JSON.parse(JSON.stringify(largeConfig));
    const afterLarge = process.memoryUsage();

    const largeDelta = afterLarge.heapUsed - beforeLarge.heapUsed;
    logger.performance(`Large data handling: ${(largeDelta / 1024 / 1024).toFixed(2)}MB`);

    if (largeDelta > 200 * 1024 * 1024) { // 200MB
      logger.warn('Large data handling uses excessive memory');
    }

  } catch (error) {
    logger.debug(`Large data test error: ${error.message}`);
  }

  logger.debug('Memory usage analysis completed');
}

/**
 * Test cache performance optimization
 */
async function testCachePerformanceOptimization(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing cache performance optimization...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test cache hit ratio
  sopsHelper.clearCache();

  const cacheTests = [
    { name: 'Cache miss (first load)', env: 'dev' },
    { name: 'Cache hit (second load)', env: 'dev' },
    { name: 'Cache miss (different env)', env: 'stg' },
    { name: 'Cache hit (repeated env)', env: 'stg' },
    { name: 'Cache hit (back to first)', env: 'dev' }
  ];

  const cacheResults = [];

  for (const test of cacheTests) {
    const startTime = process.hrtime.bigint();

    try {
      await sopsHelper.getEnvironmentConfig('r2', test.env, true);

      const endTime = process.hrtime.bigint();
      const duration = Number(endTime - startTime) / 1000000;

      const stats = sopsHelper.getCacheStats();
      cacheResults.push({
        test: test.name,
        duration: duration,
        cacheStats: { ...stats }
      });

      logger.performance(`${test.name}: ${duration.toFixed(2)}ms (cache: ${stats.hits}h/${stats.misses}m)`);

    } catch (error) {
      logger.debug(`Cache test error: ${test.name} - ${error.message}`);
    }
  }

  // Analyze cache efficiency
  const finalStats = sopsHelper.getCacheStats();
  const hitRatio = finalStats.hits / (finalStats.hits + finalStats.misses);

  logger.performance(`Cache hit ratio: ${(hitRatio * 100).toFixed(1)}% (${finalStats.hits}/${finalStats.hits + finalStats.misses})`);

  if (hitRatio < 0.6) {
    logger.warn('Cache hit ratio is low - review caching strategy');
  }

  // Test cache performance with different sizes
  const originalCacheSize = sopsHelper.CONFIG.maxCacheSize;

  const cacheSizeTests = [5, 10, 20, 50];

  for (const cacheSize of cacheSizeTests) {
    sopsHelper.CONFIG.maxCacheSize = cacheSize;
    sopsHelper.clearCache();

    const startTime = Date.now();

    // Load multiple configurations
    for (let i = 0; i < cacheSize + 5; i++) {
      const env = ['dev', 'stg', 'prod'][i % 3];
      await sopsHelper.getEnvironmentConfig('r2', env, true);
    }

    const duration = Date.now() - startTime;
    const stats = sopsHelper.getCacheStats();

    logger.performance(`Cache size ${cacheSize}: ${duration}ms, final size: ${stats.size}`);
  }

  // Restore original cache size
  sopsHelper.CONFIG.maxCacheSize = originalCacheSize;

  // Test cache TTL performance
  const originalTTL = sopsHelper.CONFIG.defaultCacheTTL;

  const ttlTests = [100, 1000, 5000]; // milliseconds

  for (const ttl of ttlTests) {
    sopsHelper.CONFIG.defaultCacheTTL = ttl;
    sopsHelper.clearCache();

    // Load configuration
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);

    // Wait for TTL to approach expiration
    await new Promise(resolve => setTimeout(resolve, ttl - 50));

    const beforeExpire = Date.now();
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    const beforeExpireDuration = Date.now() - beforeExpire;

    // Wait for TTL to expire
    await new Promise(resolve => setTimeout(resolve, 100));

    const afterExpire = Date.now();
    await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    const afterExpireDuration = Date.now() - afterExpire;

    logger.performance(`TTL ${ttl}ms: before expire ${beforeExpireDuration}ms, after expire ${afterExpireDuration}ms`);
  }

  // Restore original TTL
  sopsHelper.CONFIG.defaultCacheTTL = originalTTL;

  logger.debug('Cache performance optimization completed');
}

/**
 * Test concurrent operation handling
 */
async function testConcurrentOperationHandling(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing concurrent operation handling...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test concurrent cache access
  sopsHelper.clearCache();

  const concurrencyLevels = [2, 5, 10];

  for (const concurrency of concurrencyLevels) {
    logger.debug(`Testing concurrency level: ${concurrency}`);

    const startTime = Date.now();

    const promises = Array(concurrency).fill().map(async (_, index) => {
      const env = ['dev', 'stg', 'prod'][index % 3];
      return sopsHelper.getEnvironmentConfig('r2', env, true);
    });

    try {
      const results = await Promise.all(promises);
      const duration = Date.now() - startTime;

      const allSucceeded = results.every(result => result && result.cf_account_id);
      logger.performance(`Concurrency ${concurrency}: ${duration}ms, all succeeded: ${allSucceeded}`);

      if (!allSucceeded) {
        logger.warn(`Some concurrent operations failed at concurrency level ${concurrency}`);
      }

      // Check cache consistency
      const stats = sopsHelper.getCacheStats();
      logger.performance(`Cache after concurrency test: size=${stats.size}, hits=${stats.hits}, misses=${stats.misses}`);

    } catch (error) {
      logger.warn(`Concurrency test failed at level ${concurrency}: ${error.message}`);
    }
  }

  // Test concurrent command execution
  const commands = [
    'just --version',
    'nix run .#r2:envs',
    'nix run .#status'
  ];

  for (const concurrency of [2, 3, 5]) {
    logger.debug(`Testing concurrent commands: ${concurrency} processes`);

    const startTime = Date.now();

    const commandPromises = Array(concurrency).fill().map((_, index) => {
      const command = commands[index % commands.length];
      return testSuite.execCommand(command, { timeout: 30000 });
    });

    try {
      const results = await Promise.all(commandPromises);
      const duration = Date.now() - startTime;

      const successCount = results.filter(r => r.code === 0).length;
      logger.performance(`Concurrent commands ${concurrency}: ${duration}ms, ${successCount}/${concurrency} succeeded`);

      if (successCount < concurrency * 0.8) {
        logger.warn(`High failure rate in concurrent command execution: ${successCount}/${concurrency}`);
      }

    } catch (error) {
      logger.warn(`Concurrent command test failed: ${error.message}`);
    }
  }

  // Test race condition detection
  logger.debug('Testing race condition detection...');

  const raceTestIterations = 20;
  const raceResults = [];

  for (let i = 0; i < raceTestIterations; i++) {
    sopsHelper.clearCache();

    const promise1 = sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    const promise2 = sopsHelper.getEnvironmentConfig('r2', 'dev', true);

    try {
      const [result1, result2] = await Promise.all([promise1, promise2]);

      const identical = JSON.stringify(result1) === JSON.stringify(result2);
      raceResults.push(identical);

      if (!identical) {
        logger.warn(`Race condition detected in iteration ${i + 1}`);
      }

    } catch (error) {
      logger.debug(`Race test iteration ${i + 1} error: ${error.message}`);
      raceResults.push(false);
    }
  }

  const successfulRaces = raceResults.filter(r => r).length;
  const raceSuccessRate = (successfulRaces / raceTestIterations) * 100;

  logger.performance(`Race condition test: ${raceSuccessRate.toFixed(1)}% consistency (${successfulRaces}/${raceTestIterations})`);

  if (raceSuccessRate < 95) {
    logger.warn('Low consistency in concurrent access - investigate race conditions');
  }

  logger.debug('Concurrent operation handling completed');
}

/**
 * Test resource usage monitoring
 */
async function testResourceUsageMonitoring(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing resource usage monitoring...');

  // Monitor CPU usage during operations
  const cpuUsageTests = [
    { name: 'Idle state', action: () => new Promise(resolve => setTimeout(resolve, 100)) },
    { name: 'Config loading', action: () => require('../helpers/sops-yaml.js').getEnvironmentConfig('r2', 'dev', true) },
    { name: 'Manifest generation', action: () => require('../scripts/gen-connection-manifest.js').generateManifest({ environment: 'dev', useTemplate: true, dryRun: true }) },
    { name: 'Multiple operations', action: async () => {
      const sopsHelper = require('../helpers/sops-yaml.js');
      await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
      await sopsHelper.getEnvironmentConfig('r2', 'stg', true);
      await sopsHelper.getEnvironmentConfig('r2', 'prod', true);
    }}
  ];

  for (const test of cpuUsageTests) {
    const startUsage = process.cpuUsage();
    const startTime = Date.now();

    try {
      await test.action();

      const endTime = Date.now();
      const endUsage = process.cpuUsage(startUsage);

      const duration = endTime - startTime;
      const cpuTime = (endUsage.user + endUsage.system) / 1000000; // Convert to seconds

      const cpuPercent = duration > 0 ? (cpuTime / (duration / 1000)) * 100 : 0;

      logger.performance(`${test.name}: ${duration}ms, CPU: ${cpuPercent.toFixed(1)}%`);

      if (cpuPercent > 50) {
        logger.warn(`High CPU usage detected: ${test.name} - ${cpuPercent.toFixed(1)}%`);
      }

    } catch (error) {
      logger.debug(`CPU test error: ${test.name} - ${error.message}`);
    }
  }

  // Monitor file system operations
  const tempDir = testSuite.TEST_CONFIG.tempDir;

  const fileOperationTests = [
    {
      name: 'Small file write',
      action: () => {
        const filePath = path.join(tempDir, 'small-test.txt');
        fs.writeFileSync(filePath, 'test content');
        return filePath;
      }
    },
    {
      name: 'Large file write',
      action: () => {
        const filePath = path.join(tempDir, 'large-test.txt');
        const largeContent = 'x'.repeat(1024 * 1024); // 1MB
        fs.writeFileSync(filePath, largeContent);
        return filePath;
      }
    },
    {
      name: 'Multiple file operations',
      action: () => {
        const files = [];
        for (let i = 0; i < 10; i++) {
          const filePath = path.join(tempDir, `multi-test-${i}.txt`);
          fs.writeFileSync(filePath, `content ${i}`);
          files.push(filePath);
        }
        return files;
      }
    }
  ];

  for (const test of fileOperationTests) {
    const startTime = Date.now();

    try {
      const result = test.action();
      const duration = Date.now() - startTime;

      logger.performance(`${test.name}: ${duration}ms`);

      // Cleanup
      if (Array.isArray(result)) {
        result.forEach(file => fs.existsSync(file) && fs.unlinkSync(file));
      } else if (typeof result === 'string' && fs.existsSync(result)) {
        fs.unlinkSync(result);
      }

      if (duration > 1000) {
        logger.warn(`Slow file operation: ${test.name} - ${duration}ms`);
      }

    } catch (error) {
      logger.debug(`File operation test error: ${test.name} - ${error.message}`);
    }
  }

  // Monitor network-like operations (command execution)
  const networkTests = [
    { name: 'Fast command', command: 'just --version' },
    { name: 'Medium command', command: 'just --list' },
    { name: 'Complex command', command: 'nix run .#status' }
  ];

  for (const test of networkTests) {
    const startTime = Date.now();

    try {
      const result = await testSuite.execCommand(test.command, { timeout: 30000 });
      const duration = Date.now() - startTime;

      logger.performance(`${test.name}: ${duration}ms (exit code: ${result.code})`);

      if (duration > 5000 && result.code === 0) {
        logger.warn(`Slow network-like operation: ${test.name} - ${duration}ms`);
      }

    } catch (error) {
      logger.debug(`Network test error: ${test.name} - ${error.message}`);
    }
  }

  logger.debug('Resource usage monitoring completed');
}

/**
 * Test scalability testing
 */
async function testScalabilityTesting(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing scalability...');

  const sopsHelper = require('../helpers/sops-yaml.js');

  // Test configuration loading scalability
  const configCounts = [1, 5, 10, 25, 50];

  for (const count of configCounts) {
    logger.debug(`Testing scalability with ${count} configuration loads`);

    sopsHelper.clearCache();
    const startTime = Date.now();
    const startMemory = process.memoryUsage();

    try {
      const promises = [];
      for (let i = 0; i < count; i++) {
        const env = ['dev', 'stg', 'prod'][i % 3];
        promises.push(sopsHelper.getEnvironmentConfig('r2', env, true));
      }

      await Promise.all(promises);

      const endTime = Date.now();
      const endMemory = process.memoryUsage();

      const duration = endTime - startTime;
      const memoryDelta = endMemory.heapUsed - startMemory.heapUsed;
      const avgDuration = duration / count;

      logger.performance(`${count} configs: ${duration}ms total, ${avgDuration.toFixed(2)}ms avg, ${(memoryDelta / 1024 / 1024).toFixed(2)}MB memory`);

      // Check for linear scaling
      if (count > 1) {
        const expectedDuration = avgDuration * count;
        const efficiency = expectedDuration / duration;

        if (efficiency < 0.5) {
          logger.warn(`Poor scaling efficiency at ${count} configs: ${(efficiency * 100).toFixed(1)}%`);
        }
      }

    } catch (error) {
      logger.warn(`Scalability test failed at ${count} configs: ${error.message}`);
    }
  }

  // Test cache scalability
  const cacheScalabilityTests = [10, 50, 100];

  for (const cacheSize of cacheScalabilityTests) {
    logger.debug(`Testing cache scalability with ${cacheSize} entries`);

    sopsHelper.CONFIG.maxCacheSize = cacheSize;
    sopsHelper.clearCache();

    const startTime = Date.now();

    // Fill cache to capacity
    for (let i = 0; i < cacheSize; i++) {
      const env = ['dev', 'stg', 'prod'][i % 3];
      const variant = Math.floor(i / 3);
      await sopsHelper.getEnvironmentConfig('r2', env, true, { variant });
    }

    const fillTime = Date.now() - startTime;

    // Test access performance
    const accessStart = Date.now();
    for (let i = 0; i < 10; i++) {
      await sopsHelper.getEnvironmentConfig('r2', 'dev', true);
    }
    const accessTime = Date.now() - accessStart;

    const stats = sopsHelper.getCacheStats();

    logger.performance(`Cache ${cacheSize}: fill=${fillTime}ms, access=${accessTime}ms, final size=${stats.size}`);

    if (accessTime > fillTime * 0.1) {
      logger.warn(`Cache access time increasing with size: ${accessTime}ms vs ${fillTime}ms fill time`);
    }
  }

  // Test command execution scalability
  const commandScalabilityTests = [
    { command: 'just --version', scales: [1, 3, 5] },
    { command: 'nix run .#r2:envs', scales: [1, 2, 3] }
  ];

  for (const test of commandScalabilityTests) {
    for (const scale of test.scales) {
      logger.debug(`Testing command scalability: ${test.command} x${scale}`);

      const startTime = Date.now();

      try {
        const promises = Array(scale).fill().map(() =>
          testSuite.execCommand(test.command, { timeout: 30000 })
        );

        const results = await Promise.all(promises);
        const duration = Date.now() - startTime;

        const successCount = results.filter(r => r.code === 0).length;
        const avgDuration = duration / scale;

        logger.performance(`${test.command} x${scale}: ${duration}ms total, ${avgDuration.toFixed(2)}ms avg, ${successCount}/${scale} succeeded`);

      } catch (error) {
        logger.warn(`Command scalability test failed: ${test.command} x${scale} - ${error.message}`);
      }
    }
  }

  logger.debug('Scalability testing completed');
}

/**
 * Test I/O performance analysis
 */
async function testIOPerformanceAnalysis(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing I/O performance...');

  const tempDir = testSuite.TEST_CONFIG.tempDir;

  // Test file I/O performance
  const fileSizes = [1024, 10240, 102400, 1048576]; // 1KB, 10KB, 100KB, 1MB

  for (const size of fileSizes) {
    const content = 'x'.repeat(size);
    const filePath = path.join(tempDir, `io-test-${size}.txt`);

    try {
      // Test write performance
      const writeStart = Date.now();
      fs.writeFileSync(filePath, content);
      const writeTime = Date.now() - writeStart;

      // Test read performance
      const readStart = Date.now();
      const readContent = fs.readFileSync(filePath, 'utf8');
      const readTime = Date.now() - readStart;

      // Verify integrity
      const integrity = readContent === content;

      logger.performance(`File I/O ${(size / 1024).toFixed(1)}KB: write=${writeTime}ms, read=${readTime}ms, integrity=${integrity}`);

      if (writeTime > 100 || readTime > 100) {
        logger.warn(`Slow file I/O for ${(size / 1024).toFixed(1)}KB: write=${writeTime}ms, read=${readTime}ms`);
      }

      // Cleanup
      fs.unlinkSync(filePath);

    } catch (error) {
      logger.debug(`File I/O test error for ${size} bytes: ${error.message}`);
    }
  }

  // Test concurrent file operations
  const concurrentFileTests = [2, 5, 10];

  for (const concurrency of concurrentFileTests) {
    logger.debug(`Testing concurrent file I/O: ${concurrency} operations`);

    const startTime = Date.now();

    try {
      const promises = Array(concurrency).fill().map(async (_, index) => {
        const filePath = path.join(tempDir, `concurrent-${index}.txt`);
        const content = `content for file ${index}`;

        fs.writeFileSync(filePath, content);
        const readBack = fs.readFileSync(filePath, 'utf8');

        fs.unlinkSync(filePath);

        return readBack === content;
      });

      const results = await Promise.all(promises);
      const duration = Date.now() - startTime;

      const successCount = results.filter(r => r).length;

      logger.performance(`Concurrent file I/O x${concurrency}: ${duration}ms, ${successCount}/${concurrency} succeeded`);

      if (successCount < concurrency) {
        logger.warn(`File I/O failures in concurrent test: ${successCount}/${concurrency}`);
      }

    } catch (error) {
      logger.warn(`Concurrent file I/O test failed: ${error.message}`);
    }
  }

  // Test directory operations
  const dirOperationTests = [
    {
      name: 'Directory creation',
      action: () => {
        const dirPath = path.join(tempDir, 'test-dir');
        fs.mkdirSync(dirPath);
        return dirPath;
      }
    },
    {
      name: 'Directory listing',
      action: () => {
        return fs.readdirSync(tempDir);
      }
    },
    {
      name: 'Directory stats',
      action: () => {
        return fs.statSync(tempDir);
      }
    }
  ];

  for (const test of dirOperationTests) {
    const startTime = Date.now();

    try {
      const result = test.action();
      const duration = Date.now() - startTime;

      logger.performance(`${test.name}: ${duration}ms`);

      if (duration > 100) {
        logger.warn(`Slow directory operation: ${test.name} - ${duration}ms`);
      }

      // Cleanup if needed
      if (typeof result === 'string' && fs.existsSync(result)) {
        const stats = fs.statSync(result);
        if (stats.isDirectory()) {
          fs.rmdirSync(result);
        }
      }

    } catch (error) {
      logger.debug(`Directory operation test error: ${test.name} - ${error.message}`);
    }
  }

  logger.debug('I/O performance analysis completed');
}

/**
 * Test performance regression detection
 */
async function testPerformanceRegressionDetection(testSuite) {
  const { logger } = testSuite;

  logger.debug('Testing performance regression detection...');

  // Define performance baselines (these would be updated over time)
  const performanceBaselines = {
    'just --version': { max: 500, avg: 200 }, // milliseconds
    'just --list': { max: 1000, avg: 500 },
    'nix run .#status': { max: 5000, avg: 2000 },
    'config-load-dev': { max: 1000, avg: 300 },
    'manifest-generation': { max: 2000, avg: 800 }
  };

  const regressionResults = [];

  // Test command performance against baselines
  const commandTests = [
    { name: 'just --version', command: 'just --version' },
    { name: 'just --list', command: 'just --list' },
    { name: 'nix run .#status', command: 'nix run .#status' }
  ];

  for (const test of commandTests) {
    const baseline = performanceBaselines[test.name];
    if (!baseline) continue;

    const iterations = 5;
    const times = [];

    for (let i = 0; i < iterations; i++) {
      try {
        const startTime = Date.now();
        const result = await testSuite.execCommand(test.command, { timeout: 30000 });
        const duration = Date.now() - startTime;

        if (result.code === 0) {
          times.push(duration);
        }
      } catch (error) {
        logger.debug(`Performance test error: ${test.name} - ${error.message}`);
      }
    }

    if (times.length > 0) {
      const stats = calculatePerformanceStats(times);
      const regression = {
        test: test.name,
        current: stats,
        baseline: baseline,
        maxRegression: stats.max > baseline.max,
        avgRegression: stats.average > baseline.avg
      };

      regressionResults.push(regression);

      if (regression.maxRegression || regression.avgRegression) {
        logger.warn(`Performance regression detected in ${test.name}: avg=${stats.average.toFixed(2)}ms (baseline: ${baseline.avg}ms), max=${stats.max.toFixed(2)}ms (baseline: ${baseline.max}ms)`);
      } else {
        logger.performance(`Performance within baseline for ${test.name}: avg=${stats.average.toFixed(2)}ms, max=${stats.max.toFixed(2)}ms`);
      }
    }
  }

  // Test functional performance against baselines
  const functionalTests = [
    {
      name: 'config-load-dev',
      action: () => require('../helpers/sops-yaml.js').getEnvironmentConfig('r2', 'dev', true)
    },
    {
      name: 'manifest-generation',
      action: () => require('../scripts/gen-connection-manifest.js').generateManifest({
        environment: 'dev',
        useTemplate: true,
        dryRun: true
      })
    }
  ];

  for (const test of functionalTests) {
    const baseline = performanceBaselines[test.name];
    if (!baseline) continue;

    const iterations = 3;
    const times = [];

    for (let i = 0; i < iterations; i++) {
      try {
        const startTime = Date.now();
        await test.action();
        const duration = Date.now() - startTime;
        times.push(duration);
      } catch (error) {
        logger.debug(`Functional performance test error: ${test.name} - ${error.message}`);
      }
    }

    if (times.length > 0) {
      const stats = calculatePerformanceStats(times);
      const regression = {
        test: test.name,
        current: stats,
        baseline: baseline,
        maxRegression: stats.max > baseline.max,
        avgRegression: stats.average > baseline.avg
      };

      regressionResults.push(regression);

      if (regression.maxRegression || regression.avgRegression) {
        logger.warn(`Functional performance regression detected in ${test.name}: avg=${stats.average.toFixed(2)}ms (baseline: ${baseline.avg}ms), max=${stats.max.toFixed(2)}ms (baseline: ${baseline.max}ms)`);
      } else {
        logger.performance(`Functional performance within baseline for ${test.name}: avg=${stats.average.toFixed(2)}ms, max=${stats.max.toFixed(2)}ms`);
      }
    }
  }

  // Generate performance report
  const regressions = regressionResults.filter(r => r.maxRegression || r.avgRegression);
  const improvements = regressionResults.filter(r => r.current.average < r.baseline.avg * 0.9);

  logger.performance(`Performance summary: ${regressions.length} regressions, ${improvements.length} improvements out of ${regressionResults.length} tests`);

  if (regressions.length > 0) {
    logger.warn(`Performance regressions detected in: ${regressions.map(r => r.test).join(', ')}`);
  }

  if (improvements.length > 0) {
    logger.performance(`Performance improvements in: ${improvements.map(r => r.test).join(', ')}`);
  }

  // Save performance data for historical tracking
  const performanceReport = {
    timestamp: new Date().toISOString(),
    results: regressionResults,
    summary: {
      total: regressionResults.length,
      regressions: regressions.length,
      improvements: improvements.length
    }
  };

  const reportPath = path.join(testSuite.TEST_CONFIG.tempDir, 'performance-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(performanceReport, null, 2));

  logger.debug(`Performance report saved to: ${reportPath}`);

  logger.debug('Performance regression detection completed');
}

/**
 * Measure execution time of an async function
 */
async function measureExecutionTime(asyncFn) {
  const startTime = Date.now();

  try {
    const result = await asyncFn();
    const duration = Date.now() - startTime;

    return {
      success: true,
      duration: duration,
      result: result
    };
  } catch (error) {
    const duration = Date.now() - startTime;

    return {
      success: false,
      duration: duration,
      error: error.message
    };
  }
}

/**
 * Calculate performance statistics from an array of times
 */
function calculatePerformanceStats(times) {
  if (times.length === 0) {
    return { min: 0, max: 0, average: 0, median: 0, stddev: 0 };
  }

  const sorted = [...times].sort((a, b) => a - b);
  const sum = times.reduce((a, b) => a + b, 0);
  const average = sum / times.length;

  const variance = times.reduce((acc, time) => acc + Math.pow(time - average, 2), 0) / times.length;
  const stddev = Math.sqrt(variance);

  const median = sorted.length % 2 === 0
    ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : sorted[Math.floor(sorted.length / 2)];

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    average: average,
    median: median,
    stddev: stddev
  };
}

/**
 * Format memory usage for display
 */
function formatMemoryUsage(memUsage) {
  return `RSS: ${(memUsage.rss / 1024 / 1024).toFixed(2)}MB, Heap: ${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB/${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB, External: ${(memUsage.external / 1024 / 1024).toFixed(2)}MB`;
}

/**
 * Format memory delta for display
 */
function formatMemoryDelta(memDelta) {
  return `RSS: ${(memDelta.rss / 1024 / 1024).toFixed(2)}MB, Heap: ${(memDelta.heapUsed / 1024 / 1024).toFixed(2)}MB, External: ${(memDelta.external / 1024 / 1024).toFixed(2)}MB`;
}

module.exports = {
  runTests,
  testCommandExecutionPerformance,
  testMemoryUsageAnalysis,
  testCachePerformanceOptimization,
  testConcurrentOperationHandling,
  testResourceUsageMonitoring,
  testScalabilityTesting,
  testIOPerformanceAnalysis,
  testPerformanceRegressionDetection,
  measureExecutionTime,
  calculatePerformanceStats,
  formatMemoryUsage,
  formatMemoryDelta,
};
