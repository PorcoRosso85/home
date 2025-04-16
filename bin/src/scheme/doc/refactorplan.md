# cli.ts リファクタリング計画

## 現状の問題点
1. インターフェース部分とロジック部分が混在している
2. 責務が明確に分離されていない
3. テスト容易性が低い
4. 拡張性が制限されている

## リファクタリング目標
1. クリーンアーキテクチャに基づいた構造設計
2. 責務の明確な分離
3. テスト容易性の向上
4. 拡張性の確保

## 新しいディレクトリ構造（戦略的DDDアプローチ）
```
src/
├── interface/
│   ├── cliController.ts
│   └── displayHelper.ts
│
├── application/
│   ├── registerCommand.ts
│   ├── generateCommand.ts
│   ├── validateCommand.ts
│   ├── diagnoseCommand.ts
│   ├── listCommand.ts
│   ├── metaSchemaRegistryService.ts
│   ├── schemaGenerationUseCase.ts
│   ├── schemaValidationUseCase.ts
│   └── configDiagnosisUseCase.ts
│
├── domain/
│   ├── metaSchema.ts
│   ├── schema.ts
│   ├── config.ts
│   ├── metaSchemaRepository.ts
│   ├── validationService.ts
│   └── generationService.ts
│
└── infrastructure/
    ├── fileMetaSchemaRepository.ts
    ├── fileSystemReader.ts
    └── fileSystemWriter.ts
```

## リファクタリング手順

### 1. ドメインの実装
- MetaSchema, Schema, Configなどの中核オブジェクトを定義
- 検証ロジックをドメインサービスに実装

### 2. リポジトリインターフェースの定義
- メタスキーマの検索、取得などのインターフェースを定義
- ファイルシステムベースのリポジトリ実装

### 3. アプリケーションサービスの実装
- メタスキーマレジストリのサービス化
- ユースケース（生成、検証、診断）の実装
- コマンドハンドラーの実装

### 4. UI層の実装
- コマンドライン引数の解析と対応するユースケースへの委譲
- 表示用ヘルパーの実装

## 主要なリファクタリングポイント

### 1. MetaSchemaHandlerをより適切なドメインオブジェクトに変更
```typescript
// Before:
interface MetaSchemaHandler {
  validate(schema: any): ValidationResult;
  validateConfig(config: any): ValidationResult;
  generate(config: any): any;
  transform?(fromSchema: any, toMetaSchema: string): any;
}

// After:
// domain/metaSchema.ts
interface MetaSchema {
  id: string;
  title: string;
  schema: Record<string, any>;
}

// domain/validationService.ts
interface ValidationService {
  validateSchema(schema: any, metaSchema: MetaSchema): ValidationResult;
  validateConfig(config: any, metaSchema: MetaSchema): ValidationResult;
}

// domain/generationService.ts
interface GenerationService {
  generateSchema(config: any, metaSchema: MetaSchema): any;
}
```

### 2. MetaSchemaRegistryをアプリケーションサービスに移行
```typescript
// Before:
class MetaSchemaRegistry {
  private handlers: Map<string, MetaSchemaHandler> = new Map();
  private schemas: Map<string, any> = new Map();
  // ...
}

// After:
// application/metaSchemaRegistryService.ts
class MetaSchemaRegistryService {
  constructor(
    private metaSchemaRepository: MetaSchemaRepository,
    private validationService: ValidationService,
    private generationService: GenerationService
  ) {}

  async registerMetaSchema(metaSchema: MetaSchema): Promise<void> {
    // ...
  }

  async validateSchema(schema: any): Promise<ValidationResult> {
    // ...
  }

  async generateSchema(metaSchemaId: string, config: any): Promise<any> {
    // ...
  }
}
```

### 3. コマンドハンドラーの分離
```typescript
// Before:
async function main() {
  // コマンドライン引数の解析
  const args = parse(Deno.args, {
    boolean: ['help', 'verbose'],
    alias: { h: 'help', v: 'verbose' },
  });
  
  // 長い switch 文...
}

// After:
// interface/cliController.ts
async function main() {
  const args = parse(Deno.args, {
    boolean: ['help', 'verbose'],
    alias: { h: 'help', v: 'verbose' },
  });
  
  const command = args._[0] as string;
  
  try {
    switch (command) {
      case "register":
        return await registerCommand.execute(args);
      case "generate":
        return await generateCommand.execute(args);
      // ...
    }
  } catch (error) {
    displayError(error.message);
  }
}

// application/registerCommand.ts
class RegisterCommand {
  constructor(private registryService: MetaSchemaRegistryService) {}
  
  async execute(args: any): Promise<void> {
    // 実装...
  }
}
```

## 期待される効果

1. 関心の分離による保守性の向上
2. ドメインロジックの独立化による再利用性の向上
3. テスト容易性の向上（モックが容易に）
4. 拡張性の向上（新しいメタスキーマタイプの追加が容易に）
5. 依存関係の一方向性の確保（内側の層は外側の層に依存しない）
