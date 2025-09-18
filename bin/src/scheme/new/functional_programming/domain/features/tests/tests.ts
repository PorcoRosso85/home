/**
 * @file tests.ts
 * @description 関数型スキーマにテスト情報を含めるための型定義
 */

/**
 * テスト関連機能のインターフェース
 */
export type TestsFeature = {
  // テストが必要かどうかのフラグ情報
  requiresTests: boolean;
  
  // テストケース生成のヒント情報
  testCaseGeneration?: {
    // エッジケースの識別情報
    edgeCases?: Array<{
      description: string;
      input?: any;
      expectedOutput?: any;
    }>;
    
    // 境界条件の明示
    boundaryConditions?: Array<{
      description: string;
      input?: any;
      expectedOutput?: any;
    }>;
    
    // 必須の正常系テストケース
    essentialHappyPath?: {
      description: string;
      input?: any;
      expectedOutput?: any;
      motivation?: string; // なぜこのテストが重要か
    };
  };
  
  // プロパティベーステストの戦略
  propertyBasedTesting?: {
    // 生成すべき入力の性質
    inputProperties?: Array<{
      property: string;
      description: string;
    }>;
    
    // 不変条件の定義
    invariants?: Array<{
      description: string;
      condition?: string;
    }>;
  };
  
  // テスト容易性の評価基準
  testability?: {
    // モック化の可能性
    mockability?: {
      score: number; // 1-10のスケール
      description?: string;
    };
    
    // 分離テスト戦略
    isolationStrategy?: {
      description: string;
      dependencies?: string[];
    };
  };
};

/**
 * テスト機能の作成関数
 */
export const createTestsFeature = (
  requiresTests: boolean,
  options: Partial<Omit<TestsFeature, 'requiresTests'>> = {}
): TestsFeature => {
  return {
    requiresTests,
    ...options
  };
};
