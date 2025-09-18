#!/usr/bin/env bun
import { CommandValidator, GoProducerContract, BunConsumerContract } from './src/contracts/command-contract';

console.log('=== Contract Validation Test ===\n');

const validator = new CommandValidator();

// Test 1: Valid compatibility
console.log('Test 1: Valid producer-consumer compatibility');
const result1 = validator.validateCompatibility(GoProducerContract, BunConsumerContract);
console.log('Result:', result1);
console.log('Expected: { valid: true }\n');

// Test 2: Invalid - missing command
console.log('Test 2: Invalid - consumer requires non-existent command');
const invalidConsumer = {
  ...BunConsumerContract,
  commands: {
    missing: {
      command: 'non-existent-command',
      version: '1.0.0',
      capabilities: ['unknown']
    }
  }
};
const result2 = validator.validateCompatibility(GoProducerContract, invalidConsumer);
console.log('Result:', result2);
console.log('Expected: Error about missing command\n');

// Test 3: Invalid - not path-managed
console.log('Test 3: Invalid - producer not path-managed');
const invalidProducer = {
  ...GoProducerContract,
  capabilities: ['pure-contract', 'data-transformer'] // removed 'path-managed'
};
const result3 = validator.validateCompatibility(invalidProducer, BunConsumerContract);
console.log('Result:', result3);
console.log('Expected: Error about path-managed requirement\n');

console.log('=== All tests completed ===');