# ブラウザ互換性対応：フェーズ1

## 概要

フェーズ1では、インフラ層をブラウザとDenoのクッション層として機能させ、その他の層（ドメイン層、サービス層、アプリケーション層）から環境依存のコードを完全に排除します。このフェーズでは、実際のブラウザ実装は行わず、インフラ層のインターフェースを整備して副作用処理を完全に隔離します。

## 目標

1. インフラ層を明確なインターフェースで定義し、環境依存コードのゲートウェイとする
2. ドメイン層、サービス層、アプリケーション層から副作用処理を完全に排除する
3. CLI と サーバー実装が新しいアーキテクチャで正常に動作することを確認する

## 実施内容

### 1. インフラ層のインターフェース定義

#### 1.1 ファイルシステム操作の抽象化

```typescript
// infrastructure/interfaces/FileSystem.ts

export interface FileSystem {
  // ファイル読み取り
  readFile(path: string): Promise<string>;
  readJsonFile<T = unknown>(path: string): Promise<T>;
  
  // ファイル書き込み
  writeFile(path: string, content: string): Promise<void>;
  writeJsonFile<T>(path: string, data: T, pretty?: boolean): Promise<void>;
  
  // ファイル操作
  exists(path: string): Promise<boolean>;
  createDirectory(path: string, recursive?: boolean): Promise<void>;
  remove(path: string): Promise<void>;
  
  // パス操作
  resolvePath(...paths: string[]): string;
  dirname(path: string): string;
  basename(path: string): string;
  join(...paths: string[]): string;
}
```

#### 1.2 環境情報の抽象化

```typescript
// infrastructure/interfaces/Environment.ts

export interface Environment {
  // 現在の作業ディレクトリ
  currentDirectory(): string;
  
  // 環境変数アクセス
  getEnvVariable(name: string): string | undefined;
  
  // 実行環境情報
  isBrowser(): boolean;
  isDeno(): boolean;
}
```

#### 1.3 ロギングの抽象化

```typescript
// infrastructure/interfaces/Logger.ts

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

export interface Logger {
  debug(message: string, ...args: any[]): void;
  info(message: string, ...args: any[]): void;
  warn(message: string, ...args: any[]): void;
  error(message: string, ...args: any[]): void;
  setLevel(level: LogLevel): void;
  getLevel(): LogLevel;
}
```

### 2. Deno向け実装の作成

現時点ではDenoのみをサポートする実装を作成します。

#### 2.1 Deno向けファイルシステム実装

```typescript
// infrastructure/deno/DenoFileSystem.ts

import { FileSystem } from '../interfaces/FileSystem.ts';
import * as path from 'node:path';

export class DenoFileSystem implements FileSystem {
  async readFile(path: string): Promise<string> {
    return await Deno.readTextFile(path);
  }
  
  async readJsonFile<T = unknown>(path: string): Promise<T> {
    const text = await this.readFile(path);
    return JSON.parse(text) as T;
  }
  
  async writeFile(path: string, content: string): Promise<void> {
    await Deno.writeTextFile(path, content);
  }
  
  async writeJsonFile<T>(path: string, data: T, pretty: boolean = true): Promise<void> {
    const text = pretty 
      ? JSON.stringify(data, null, 2) 
      : JSON.stringify(data);
    await this.writeFile(path, text);
  }
  
  async exists(path: string): Promise<boolean> {
    try {
      await Deno.stat(path);
      return true;
    } catch {
      return false;
    }
  }
  
  async createDirectory(path: string, recursive: boolean = true): Promise<void> {
    await Deno.mkdir(path, { recursive });
  }
  
  async remove(path: string): Promise<void> {
    await Deno.remove(path, { recursive: true });
  }
  
  resolvePath(...paths: string[]): string {
    return path.resolve(...paths);
  }
  
  dirname(path: string): string {
    return path.dirname(path);
  }
  
  basename(path: string): string {
    return path.basename(path);
  }
  
  join(...paths: string[]): string {
    return path.join(...paths);
  }
}
```

#### 2.2 Deno向け環境実装

```typescript
// infrastructure/deno/DenoEnvironment.ts

import { Environment } from '../interfaces/Environment.ts';

export class DenoEnvironment implements Environment {
  currentDirectory(): string {
    return Deno.cwd();
  }
  
  getEnvVariable(name: string): string | undefined {
    return Deno.env.get(name);
  }
  
  isBrowser(): boolean {
    return false;
  }
  
  isDeno(): boolean {
    return true;
  }
}
```

#### 2.3 Deno向けロガー実装

```typescript
// infrastructure/deno/DenoLogger.ts

import { Logger, LogLevel } from '../interfaces/Logger.ts';

export class DenoLogger implements Logger {
  private level: LogLevel = LogLevel.INFO;
  
  setLevel(level: LogLevel): void {
    this.level = level;
  }
  
  getLevel(): LogLevel {
    return this.level;
  }
  
  debug(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.DEBUG) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  }
  
  info(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.INFO) {
      console.info(`[INFO] ${message}`, ...args);
    }
  }
  
  warn(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.WARN) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  }
  
  error(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.ERROR) {
      console.error(`[ERROR] ${message}`, ...args);
    }
  }
}
```

### 3. インフラ層のファクトリとプロバイダー

```typescript
// infrastructure/providers/InfrastructureProvider.ts

import { FileSystem } from '../interfaces/FileSystem.ts';
import { Environment } from '../interfaces/Environment.ts';
import { Logger } from '../interfaces/Logger.ts';

import { DenoFileSystem } from '../deno/DenoFileSystem.ts';
import { DenoEnvironment } from '../deno/DenoEnvironment.ts';
import { DenoLogger } from '../deno/DenoLogger.ts';

export class InfrastructureProvider {
  private static instance: InfrastructureProvider;
  
  private fileSystem: FileSystem;
  private environment: Environment;
  private logger: Logger;
  
  private constructor() {
    // フェーズ1ではDenoのみをサポート
    this.fileSystem = new DenoFileSystem();
    this.environment = new DenoEnvironment();
    this.logger = new DenoLogger();
  }
  
  static getInstance(): InfrastructureProvider {
    if (!InfrastructureProvider.instance) {
      InfrastructureProvider.instance = new InfrastructureProvider();
    }
    return InfrastructureProvider.instance;
  }
  
  getFileSystem(): FileSystem {
    return this.fileSystem;
  }
  
  getEnvironment(): Environment {
    return this.environment;
  }
  
  getLogger(): Logger {
    return this.logger;
  }
}

// 便利なアクセサ関数
export function getFileSystem(): FileSystem {
  return InfrastructureProvider.getInstance().getFileSystem();
}

export function getEnvironment(): Environment {
  return InfrastructureProvider.getInstance().getEnvironment();
}

export function getLogger(): Logger {
  return InfrastructureProvider.getInstance().getLogger();
}
```

### 4. スキーマリポジトリの修正

```typescript
// infrastructure/repositories/SchemaFileRepository.ts

import { getFileSystem } from '../providers/InfrastructureProvider.ts';
import { FunctionSchema } from '../../domain/schema.ts';

export interface SchemaRepository {
  saveSchema(schema: FunctionSchema, outputPath: string, pretty?: boolean): Promise<void>;
  loadSchema(filePath: string): Promise<FunctionSchema>;
}

export class SchemaFileRepository implements SchemaRepository {
  private fileSystem = getFileSystem();
  
  async saveSchema(
    schema: FunctionSchema,
    outputPath: string,
    pretty: boolean = true
  ): Promise<void> {
    await this.fileSystem.writeJsonFile(outputPath, schema, pretty);
  }
  
  async loadSchema(filePath: string): Promise<FunctionSchema> {
    return await this.fileSystem.readJsonFile<FunctionSchema>(filePath);
  }
}

// シングルトンインスタンス
export const schemaRepository: SchemaRepository = new SchemaFileRepository();
```

### 5. アプリケーション層の修正

UriHandlingService を例として、process.cwd()の使用を排除します。

```typescript
// application/UriHandlingService.ts

import { ResourceUri } from '../domain/valueObjects/ResourceUri.ts';
import { ResourceUriValidationService } from '../service/ResourceUriValidationService.ts';
import { getEnvironment, getLogger } from '../infrastructure/providers/InfrastructureProvider.ts';

export interface UriHandlingServiceOptions {
  allowRelativePaths?: boolean;
  baseDirectory?: string;
}

export class UriHandlingService {
  private validationService: ResourceUriValidationService;
  private options: Required<UriHandlingServiceOptions>;
  private environment = getEnvironment();
  private logger = getLogger();
  
  constructor(options: UriHandlingServiceOptions = {}) {
    this.validationService = new ResourceUriValidationService();
    
    // 環境情報からベースディレクトリを取得
    this.options = {
      allowRelativePaths: false,
      baseDirectory: this.environment.currentDirectory(),
      ...options
    };
    
    if (this.options.allowRelativePaths) {
      this.logger.warn(
        '警告: 相対パスのサポートは将来のバージョンで削除される予定です。' +
        'URIスキーマ形式（file://）または絶対パスを使用することを推奨します。'
      );
    }
  }
  
  // ... 残りのメソッドは変更なし ...
}
```

### 6. サービス層の修正

ResourceUriValidationService を例として、console.warn の使用を排除します。

```typescript
// service/ResourceUriValidationService.ts

import { ResourceUri, ResourceUriType } from '../domain/valueObjects/ResourceUri.ts';
import { getLogger } from '../infrastructure/providers/InfrastructureProvider.ts';

export interface ResourceUriValidationResult {
  isValid: boolean;
  normalizedUri?: ResourceUri;
  errors?: string[];
}

export class ResourceUriValidationService {
  private logger = getLogger();
  
  // ... 他のメソッドは変更なし ...
  
  buildSchemaResourceUri(filePath: string, schemaName?: string): ResourceUri {
    try {
      const uri = ResourceUri.create(filePath);
      if (schemaName) {
        const baseUri = uri.value;
        return ResourceUri.create(`${baseUri}#${encodeURIComponent(schemaName)}`);
      }
      return uri;
    } catch (error) {
      if (filePath.startsWith('./') || filePath.startsWith('../')) {
        this.logger.warn('相対パスの使用は推奨されません。将来のバージョンではサポートされなくなる可能性があります。');
        const absolutePath = `/path/to/project/${filePath.replace(/^\.\//, '')}`;
        
        const uri = ResourceUri.fromAbsolutePath(absolutePath);
        if (schemaName) {
          return ResourceUri.create(`${uri.value}#${encodeURIComponent(schemaName)}`);
        }
        return uri;
      }
      
      throw error;
    }
  }
}
```

## インフラ層以外のガイドライン

このフェーズでは、以下の原則を厳守してください：

1. インフラ層以外の層では、以下を直接使用しないでください：
   - `Deno` 名前空間
   - `process` オブジェクト
   - `fs` モジュール
   - `path` モジュールの直接使用
   - `console.*` の直接使用
   - その他の環境依存コード

2. 環境依存のコードが必要な場合は、必ずインフラ層のインターフェースを経由してアクセスしてください。

3. インフラ層のインターフェースを介して提供される機能のみを使用してください：
   - ファイルシステム操作 → `getFileSystem()`
   - 環境情報 → `getEnvironment()`
   - ロギング → `getLogger()`

## 検証方法

CLI と サーバー実装が新しいアーキテクチャで正常に動作することを確認してください：

1. `interface/cli.ts` を実行して各コマンドが正常に動作することを確認
2. `interface/server.ts` を起動して API と静的ファイル配信が正常に動作することを確認

## 次のステップ

フェーズ1が完了したら、フェーズ2として以下を行います：

1. ブラウザ向けのインフラ層実装の作成
2. 環境検出とそれに基づく適切なインフラ実装の選択
3. ブラウザでの動作テスト
