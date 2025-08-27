import { describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { calculatorSpec, specMetadata } from './spec.js';
import * as calculator from './calculator.js';

// 仕様からテストを動的生成
describe(`Spec-driven tests v${specMetadata.version}`, () => {
  
  // 各仕様に対してテストスイートを生成
  for (const spec of calculatorSpec) {
    describe(`${spec.name}: ${spec.description}`, () => {
      
      // 実装が存在するか確認
      const implementation = (calculator as any)[spec.name];
      if (!implementation) {
        test.skip(`実装が未定義: ${spec.name}`, () => {});
      } else {
      
        // 各テストケースを動的に生成
        for (const testCase of spec.cases) {
          test(testCase.description, () => {
            const result = implementation(...testCase.input);
            assert.strictEqual(result, testCase.expected, 
              `Input: ${JSON.stringify(testCase.input)} → Expected: ${testCase.expected}, Got: ${result}`
            );
          });
        }
      }
    });
  }
  
  // 仕様のカバレッジチェック
  describe('Specification coverage', () => {
    test('すべての仕様関数が実装されている', () => {
      const specFunctions = calculatorSpec.map(s => s.name);
      const implementedFunctions = Object.keys(calculator);
      
      const missing = specFunctions.filter(f => !implementedFunctions.includes(f));
      assert.strictEqual(missing.length, 0, 
        `未実装の仕様: ${missing.join(', ')}`
      );
    });
    
    test('実装が仕様にない関数を含んでいない', () => {
      const specFunctions = calculatorSpec.map(s => s.name);
      const implementedFunctions = Object.keys(calculator);
      
      const extra = implementedFunctions.filter(f => !specFunctions.includes(f));
      assert.strictEqual(extra.length, 0, 
        `仕様にない実装: ${extra.join(', ')}`
      );
    });
  });
});