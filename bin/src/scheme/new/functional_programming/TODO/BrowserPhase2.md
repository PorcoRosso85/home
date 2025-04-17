# ブラウザ互換性対応：フェーズ2

## 概要

フェーズ2では、フェーズ1で構築したインフラ層の抽象化に基づき、ブラウザ環境での動作を実現します。動作ランタイム（Deno/ブラウザ）に応じてインフラ層の実装を自動的に切り替える機能を実装し、ブラウザ互換の実装を提供します。

## 目標

1. ブラウザ向けインフラ層実装の作成
2. 実行環境の自動検出と適切な実装の選択
3. ブラウザ環境での動作確認

## 実施内容

### 1. 環境検出機能の強化

```typescript
// infrastructure/utils/RuntimeDetector.ts

export enum Runtime {
  BROWSER = 'browser',
  DENO = 'deno',
  NODE = 'node',
  UNKNOWN = 'unknown'
}

export class RuntimeDetector {
  /**
   * 現在の実行環境を検出
   */
  static detect(): Runtime {
    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
      return Runtime.BROWSER;
    }
    
    if (typeof Deno !== 'undefined') {
      return Runtime.DENO;
    }
    
    if (typeof process !== 'undefined' && typeof process.versions !== 'undefined') {
      return Runtime.NODE;
    }
    
    return Runtime.UNKNOWN;
  }
  
  /**
   * ブラウザ環境かどうか
   */
  static isBrowser(): boolean {
    return this.detect() === Runtime.BROWSER;
  }
  
  /**
   * Deno環境かどうか
   */
  static isDeno(): boolean {
    return this.detect() === Runtime.DENO;
  }
  
  /**
   * Node.js環境かどうか
   */
  static isNode(): boolean {
    return this.detect() === Runtime.NODE;
  }
}
```

### 2. ブラウザ向けインフラ層実装

#### 2.1 ブラウザ向けファイルシステム実装

```typescript
// infrastructure/browser/BrowserFileSystem.ts

import { FileSystem } from '../interfaces/FileSystem.ts';
import { getLogger } from '../providers/InfrastructureProvider.ts';
import { StorageType } from './BrowserStorage.ts';

export interface BrowserFileSystemOptions {
  baseUrl?: string;
  storageType?: StorageType;
  enableCaching?: boolean;
}

export class BrowserFileSystem implements FileSystem {
  private baseUrl: string;
  private storageType: StorageType;
  private enableCaching: boolean;
  private cache: Map<string, string> = new Map();
  private logger = getLogger();
  
  constructor(options: BrowserFileSystemOptions = {}) {
    this.baseUrl = options.baseUrl || '/schemas/';
    this.storageType = options.storageType || StorageType.LOCAL_STORAGE;
    this.enableCaching = options.enableCaching !== false;
  }
  
  /**
   * ファイルを読み込む
   * 
   * 1. キャッシュをチェック
   * 2. ローカルストレージをチェック
   * 3. サーバーからフェッチ
   */
  async readFile(path: string): Promise<string> {
    // 正規化されたパス
    const normalizedPath = this.normalizePath(path);
    
    // 1. キャッシュをチェック
    if (this.enableCaching && this.cache.has(normalizedPath)) {
      return this.cache.get(normalizedPath)!;
    }
    
    // 2. ローカルストレージをチェック
    const storageKey = `fs:${normalizedPath}`;
    const storedValue = localStorage.getItem(storageKey);
    if (storedValue) {
      if (this.enableCaching) {
        this.cache.set(normalizedPath, storedValue);
      }
      return storedValue;
    }
    
    // 3. サーバーからフェッチ
    try {
      const url = this.pathToUrl(normalizedPath);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status} - ${response.statusText}`);
      }
      
      const text = await response.text();
      
      // キャッシュと永続化
      if (this.enableCaching) {
        this.cache.set(normalizedPath, text);
      }
      
      // ローカルストレージに保存
      try {
        localStorage.setItem(storageKey, text);
      } catch (e) {
        this.logger.warn(`ローカルストレージへの保存に失敗しました: ${e}`);
      }
      
      return text;
    } catch (error) {
      this.logger.error(`ファイル読み込みエラー: ${error}`);
      throw new Error(`ファイル '${normalizedPath}' の読み込みに失敗しました: ${error}`);
    }
  }
  
  /**
   * JSONファイルを読み込む
   */
  async readJsonFile<T = unknown>(path: string): Promise<T> {
    const text = await this.readFile(path);
    try {
      return JSON.parse(text) as T;
    } catch (error) {
      throw new Error(`JSONパースエラー: ${path} - ${error}`);
    }
  }
  
  /**
   * ファイルを書き込む
   * 
   * ブラウザ環境ではローカルストレージに書き込む
   */
  async writeFile(path: string, content: string): Promise<void> {
    const normalizedPath = this.normalizePath(path);
    const storageKey = `fs:${normalizedPath}`;
    
    try {
      localStorage.setItem(storageKey, content);
      
      if (this.enableCaching) {
        this.cache.set(normalizedPath, content);
      }
    } catch (error) {
      this.logger.error(`ファイル書き込みエラー: ${error}`);
      throw new Error(`ファイル '${normalizedPath}' の書き込みに失敗しました: ${error}`);
    }
  }
  
  /**
   * JSONファイルを書き込む
   */
  async writeJsonFile<T>(path: string, data: T, pretty: boolean = true): Promise<void> {
    const text = pretty 
      ? JSON.stringify(data, null, 2) 
      : JSON.stringify(data);
      
    await this.writeFile(path, text);
  }
  
  /**
   * ファイルの存在を確認
   */
  async exists(path: string): Promise<boolean> {
    const normalizedPath = this.normalizePath(path);
    
    // キャッシュをチェック
    if (this.enableCaching && this.cache.has(normalizedPath)) {
      return true;
    }
    
    // ローカルストレージをチェック
    const storageKey = `fs:${normalizedPath}`;
    if (localStorage.getItem(storageKey) !== null) {
      return true;
    }
    
    // サーバーにHEADリクエストを送信
    try {
      const url = this.pathToUrl(normalizedPath);
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  }
  
  /**
   * ディレクトリを作成
   * 
   * ブラウザでは実際のディレクトリは作成できないので、
   * 仮想ディレクトリを管理する
   */
  async createDirectory(path: string, recursive: boolean = true): Promise<void> {
    const normalizedPath = this.normalizePath(path);
    // 仮想ディレクトリ情報を保存
    localStorage.setItem(`dir:${normalizedPath}`, 'true');
  }
  
  /**
   * ファイルまたはディレクトリを削除
   */
  async remove(path: string): Promise<void> {
    const normalizedPath = this.normalizePath(path);
    
    // キャッシュから削除
    if (this.enableCaching) {
      this.cache.delete(normalizedPath);
    }
    
    // ローカルストレージから削除
    const fileKey = `fs:${normalizedPath}`;
    const dirKey = `dir:${normalizedPath}`;
    
    localStorage.removeItem(fileKey);
    localStorage.removeItem(dirKey);
    
    // 前方一致するキーもすべて削除（ディレクトリの場合）
    Object.keys(localStorage).forEach(key => {
      if ((key.startsWith(`fs:${normalizedPath}/`) || key.startsWith(`dir:${normalizedPath}/`))) {
        localStorage.removeItem(key);
      }
    });
  }
  
  /**
   * パスを解決
   */
  resolvePath(...paths: string[]): string {
    // シンプルな実装: 先頭の / を除去し、各パスを / で連結
    return '/' + paths
      .map(p => p.replace(/^\/+|\/+$/g, '')) // 先頭と末尾のスラッシュを削除
      .filter(p => p.length > 0)
      .join('/');
  }
  
  /**
   * ディレクトリ名を取得
   */
  dirname(path: string): string {
    const normalizedPath = this.normalizePath(path);
    const lastSlashIndex = normalizedPath.lastIndexOf('/');
    
    if (lastSlashIndex === -1) {
      return '.';
    }
    
    if (lastSlashIndex === 0) {
      return '/';
    }
    
    return normalizedPath.substring(0, lastSlashIndex);
  }
  
  /**
   * ファイル名を取得
   */
  basename(path: string): string {
    const normalizedPath = this.normalizePath(path);
    const lastSlashIndex = normalizedPath.lastIndexOf('/');
    
    if (lastSlashIndex === -1) {
      return normalizedPath;
    }
    
    return normalizedPath.substring(lastSlashIndex + 1);
  }
  
  /**
   * パスを連結
   */
  join(...paths: string[]): string {
    return paths
      .map(p => p.replace(/^\/+|\/+$/g, '')) // 先頭と末尾のスラッシュを削除
      .filter(p => p.length > 0)
      .join('/');
  }
  
  /**
   * パスを正規化
   */
  private normalizePath(path: string): string {
    // file:/// または file:// プレフィックスを除去
    if (path.startsWith('file:///')) {
      path = path.substring(8);
    } else if (path.startsWith('file://')) {
      path = path.substring(7);
    }
    
    // 絶対パスに変換
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    
    return path;
  }
  
  /**
   * パスをURLに変換
   */
  private pathToUrl(path: string): string {
    // スキーマファイルの場合
    if (path.endsWith('.json')) {
      return `${this.baseUrl}${path}`;
    }
    
    // その他のファイル
    return path;
  }
}
```

#### 2.2 ブラウザストレージの抽象化

```typescript
// infrastructure/browser/BrowserStorage.ts

export enum StorageType {
  LOCAL_STORAGE = 'localStorage',
  SESSION_STORAGE = 'sessionStorage',
  INDEXED_DB = 'indexedDB'
}

/**
 * ブラウザストレージの抽象化インターフェース
 */
export interface BrowserStorage {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
  clear(): Promise<void>;
  keys(): Promise<string[]>;
}

/**
 * LocalStorageを使用した実装
 */
export class LocalStorageAdapter implements BrowserStorage {
  async getItem(key: string): Promise<string | null> {
    return localStorage.getItem(key);
  }
  
  async setItem(key: string, value: string): Promise<void> {
    localStorage.setItem(key, value);
  }
  
  async removeItem(key: string): Promise<void> {
    localStorage.removeItem(key);
  }
  
  async clear(): Promise<void> {
    localStorage.clear();
  }
  
  async keys(): Promise<string[]> {
    return Object.keys(localStorage);
  }
}

/**
 * SessionStorageを使用した実装
 */
export class SessionStorageAdapter implements BrowserStorage {
  async getItem(key: string): Promise<string | null> {
    return sessionStorage.getItem(key);
  }
  
  async setItem(key: string, value: string): Promise<void> {
    sessionStorage.setItem(key, value);
  }
  
  async removeItem(key: string): Promise<void> {
    sessionStorage.removeItem(key);
  }
  
  async clear(): Promise<void> {
    sessionStorage.clear();
  }
  
  async keys(): Promise<string[]> {
    return Object.keys(sessionStorage);
  }
}
```

#### 2.3 ブラウザ向け環境実装

```typescript
// infrastructure/browser/BrowserEnvironment.ts

import { Environment } from '../interfaces/Environment.ts';

export class BrowserEnvironment implements Environment {
  /**
   * ブラウザでは仮想的な作業ディレクトリを返す
   */
  currentDirectory(): string {
    return '/';
  }
  
  /**
   * ブラウザでは環境変数にアクセスできないので、
   * localStorage から仮想的な環境変数を取得
   */
  getEnvVariable(name: string): string | undefined {
    return localStorage.getItem(`env:${name}`) || undefined;
  }
  
  /**
   * ブラウザ環境かどうか
   */
  isBrowser(): boolean {
    return true;
  }
  
  /**
   * Deno環境かどうか
   */
  isDeno(): boolean {
    return false;
  }
}
```

#### 2.4 ブラウザ向けロガー実装

```typescript
// infrastructure/browser/BrowserLogger.ts

import { Logger, LogLevel } from '../interfaces/Logger.ts';

export class BrowserLogger implements Logger {
  private level: LogLevel = LogLevel.INFO;
  
  setLevel(level: LogLevel): void {
    this.level = level;
  }
  
  getLevel(): LogLevel {
    return this.level;
  }
  
  debug(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.DEBUG) {
      console.debug(`%c[DEBUG] ${message}`, 'color: gray', ...args);
    }
  }
  
  info(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.INFO) {
      console.info(`%c[INFO] ${message}`, 'color: green', ...args);
    }
  }
  
  warn(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.WARN) {
      console.warn(`%c[WARN] ${message}`, 'color: orange', ...args);
    }
  }
  
  error(message: string, ...args: any[]): void {
    if (this.level <= LogLevel.ERROR) {
      console.error(`%c[ERROR] ${message}`, 'color: red; font-weight: bold', ...args);
    }
  }
}
```

### 3. インフラ層プロバイダーの拡張

環境検出に基づいて適切なインフラ実装を提供するようにプロバイダーを拡張します。

```typescript
// infrastructure/providers/InfrastructureProvider.ts

import { FileSystem } from '../interfaces/FileSystem.ts';
import { Environment } from '../interfaces/Environment.ts';
import { Logger } from '../interfaces/Logger.ts';
import { RuntimeDetector, Runtime } from '../utils/RuntimeDetector.ts';

// Deno実装
import { DenoFileSystem } from '../deno/DenoFileSystem.ts';
import { DenoEnvironment } from '../deno/DenoEnvironment.ts';
import { DenoLogger } from '../deno/DenoLogger.ts';

// ブラウザ実装
import { BrowserFileSystem } from '../browser/BrowserFileSystem.ts';
import { BrowserEnvironment } from '../browser/BrowserEnvironment.ts';
import { BrowserLogger } from '../browser/BrowserLogger.ts';

export interface InfrastructureOptions {
  runtime?: Runtime;
  browserOptions?: {
    baseUrl?: string;
    enableCaching?: boolean;
  };
}

export class InfrastructureProvider {
  private static instance: InfrastructureProvider;
  
  private runtime: Runtime;
  private fileSystem: FileSystem;
  private environment: Environment;
  private logger: Logger;
  
  private constructor(options: InfrastructureOptions = {}) {
    // 実行環境を自動検出または明示的に指定
    this.runtime = options.runtime || RuntimeDetector.detect();
    
    // 実行環境に応じて適切な実装を選択
    switch (this.runtime) {
      case Runtime.BROWSER:
        this.fileSystem = new BrowserFileSystem({
          baseUrl: options.browserOptions?.baseUrl,
          enableCaching: options.browserOptions?.enableCaching
        });
        this.environment = new BrowserEnvironment();
        this.logger = new BrowserLogger();
        break;
        
      case Runtime.DENO:
      default:
        this.fileSystem = new DenoFileSystem();
        this.environment = new DenoEnvironment();
        this.logger = new DenoLogger();
        break;
    }
  }
  
  /**
   * プロバイダーの初期化
   */
  static initialize(options: InfrastructureOptions = {}): void {
    InfrastructureProvider.instance = new InfrastructureProvider(options);
  }
  
  /**
   * インスタンスを取得
   */
  static getInstance(): InfrastructureProvider {
    if (!InfrastructureProvider.instance) {
      InfrastructureProvider.instance = new InfrastructureProvider();
    }
    return InfrastructureProvider.instance;
  }
  
  /**
   * 現在の実行環境を取得
   */
  getRuntime(): Runtime {
    return this.runtime;
  }
  
  /**
   * ファイルシステム実装を取得
   */
  getFileSystem(): FileSystem {
    return this.fileSystem;
  }
  
  /**
   * 環境情報実装を取得
   */
  getEnvironment(): Environment {
    return this.environment;
  }
  
  /**
   * ロガー実装を取得
   */
  getLogger(): Logger {
    return this.logger;
  }
}

// 便利なアクセサ関数
export function getRuntime(): Runtime {
  return InfrastructureProvider.getInstance().getRuntime();
}

export function getFileSystem(): FileSystem {
  return InfrastructureProvider.getInstance().getFileSystem();
}

export function getEnvironment(): Environment {
  return InfrastructureProvider.getInstance().getEnvironment();
}

export function getLogger(): Logger {
  return InfrastructureProvider.getInstance().getLogger();
}

// 便利な環境チェック関数
export function isBrowser(): boolean {
  return getRuntime() === Runtime.BROWSER;
}

export function isDeno(): boolean {
  return getRuntime() === Runtime.DENO;
}
```

### 4. ブラウザエントリポイントの作成

ブラウザ環境から関数型スキーマ機能を利用できるようにするためのエントリポイントを作成します。

```typescript
// browser/index.ts

// インフラ層の初期化
import { InfrastructureProvider, Runtime } from '../infrastructure/providers/InfrastructureProvider.ts';

// ブラウザ環境向けに初期化
InfrastructureProvider.initialize({
  runtime: Runtime.BROWSER,
  browserOptions: {
    baseUrl: '/schemas/',
    enableCaching: true
  }
});

// エクスポートするコンポーネント
export { SchemaRepository } from '../infrastructure/repositories/SchemaFileRepository.ts';
export { UriHandlingService } from '../application/UriHandlingService.ts';
export { ResourceUri, ResourceUriType } from '../domain/valueObjects/ResourceUri.ts';
export { FunctionSchema } from '../domain/schema.ts';

// 便利な関数をエクスポート
export { getLogger, getFileSystem, getEnvironment } from '../infrastructure/providers/InfrastructureProvider.ts';
```
### 5. スキーマビューアーのブラウザ対応

```typescript
// frontend/js/schemaLoader.js

/**
 * スキーマファイルをロードして表示する
 */
class SchemaLoader {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || '/schemas/';
    this.cacheEnabled = options.cacheEnabled !== false;
    this.schemaCache = new Map();
  }
  
  /**
   * スキーマファイルをロード
   */
  async loadSchema(schemaPath) {
    // キャッシュチェック
    if (this.cacheEnabled && this.schemaCache.has(schemaPath)) {
      return this.schemaCache.get(schemaPath);
    }
    
    // ローカルストレージチェック
    const storageKey = `schema:${schemaPath}`;
    const cachedSchema = localStorage.getItem(storageKey);
    if (cachedSchema) {
      try {
        const schema = JSON.parse(cachedSchema);
        if (this.cacheEnabled) {
          this.schemaCache.set(schemaPath, schema);
        }
        return schema;
      } catch (e) {
        console.warn(`Cached schema parse error: ${e}`);
        // キャッシュ削除して続行
        localStorage.removeItem(storageKey);
      }
    }
    
    // サーバーからロード
    try {
      const url = `${this.baseUrl}${schemaPath}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to load schema: ${response.status} ${response.statusText}`);
      }
      
      const schema = await response.json();
      
      // キャッシュに保存
      if (this.cacheEnabled) {
        this.schemaCache.set(schemaPath, schema);
      }
      
      // ローカルストレージに保存
      try {
        localStorage.setItem(storageKey, JSON.stringify(schema));
      } catch (e) {
        console.warn(`Failed to cache schema: ${e}`);
      }
      
      return schema;
    } catch (error) {
      console.error(`Schema load error: ${error}`);
      throw error;
    }
  }
  
  /**
   * Function__Meta.jsonからすべての関数データを抽出
   */
  async getFunctionData() {
    try {
      const metaSchema = await this.loadSchema('Function__Meta.json');
      return this.extractFunctionData(metaSchema);
    } catch (error) {
      console.error('Failed to get function data:', error);
      throw error;
    }
  }
  /**
   * メタスキーマから関数データを抽出
   */
  extractFunctionData(metaSchema) {
    // 実装は省略
    // ...
  }
  
  /**
   * 依存関係グラフデータを取得
   */
  async getGraphData() {
    try {
      const metaSchema = await this.loadSchema('Function__Meta.json');
      return this.buildGraphData(metaSchema);
    } catch (error) {
      console.error('Failed to get graph data:', error);
      throw error;
    }
  }
  
  /**
   * グラフデータを構築
   */
  buildGraphData(metaSchema) {
    // 実装は省略
    // ...
  }
}

// グローバルインスタンス
window.schemaLoader = new SchemaLoader();
```

### 6. フロントエンドコンポーネントのサーバー依存の削除

現在のフロントエンドアプリケーションのコンポーネントから、サーバーAPIへの依存を削除し、ローカルスキーマローダーを使用するように修正します。

```javascript
// frontend/js/app.js（該当部分のみ抜粋）

// 変更前:
fetchFunctionData() {
  // サンプルデータを使用（実際にはAPIをコールする）
  return new Promise((resolve) => {
    setTimeout(() => {
      // サンプルデータ
      const data = [
        {
          path: 'domain/service/functionDependencyAnalyzer.ts:::getFunctionDependency',
          // ...
        },
        // ...
      ];
      resolve(data);
    }, 500);
  });
}

// 変更後:
async fetchFunctionData() {
  try {
    return await window.schemaLoader.getFunctionData();
  } catch (error) {
    console.error('データロードエラー:', error);
    return []; // エラー時は空配列を返す
  }
}
```
## テストとデバッグ

### 1. ブラウザ互換テストの自動化

```javascript
// tests/browser/compatibility.test.js

describe('ブラウザ互換性テスト', () => {
  test('RuntimeDetectorがブラウザを正しく検出する', () => {
    const runtime = RuntimeDetector.detect();
    expect(runtime).toBe(Runtime.BROWSER);
  });
  
  test('BrowserFileSystemが正しく動作する', async () => {
    const fs = new BrowserFileSystem();
    
    // 書き込みと読み込み
    await fs.writeFile('/test.txt', 'Hello, Browser!');
    const content = await fs.readFile('/test.txt');
    expect(content).toBe('Hello, Browser!');
    
    // 存在チェック
    const exists = await fs.exists('/test.txt');
    expect(exists).toBe(true);
    
    // 削除
    await fs.remove('/test.txt');
    const existsAfterRemove = await fs.exists('/test.txt');
    expect(existsAfterRemove).toBe(false);
  });
  
  test('SchemaFileRepositoryがブラウザで動作する', async () => {
    const repo = new SchemaFileRepository();
    const testSchema = { name: 'TestSchema', properties: {} };
    
    await repo.saveSchema(testSchema, '/test-schema.json');
    const loadedSchema = await repo.loadSchema('/test-schema.json');
    
    expect(loadedSchema).toEqual(testSchema);
  });
});
```

### 2. ブラウザ対応のデバッグツール

```typescript
// infrastructure/utils/BrowserDebugger.ts

import { getLogger } from '../providers/InfrastructureProvider.ts';

export class BrowserDebugger {
  private static logger = getLogger();
  
  /**
   * デバッグ情報をコンソールに出力
   */
  static inspect(object: any, label: string = 'Debug'): void {
    this.logger.debug(`[${label}]`, object);
    
    if (typeof window !== 'undefined' && typeof window.console !== 'undefined') {
      // ブラウザコンソール用のリッチな表示
      console.groupCollapsed(`%c${label}`, 'color: blue; font-weight: bold;');
      console.dir(object);
      console.groupEnd();
    }
  }
  /**
   * ブラウザストレージの内容を表示
   */
  static inspectStorage(): void {
    if (typeof localStorage === 'undefined') {
      this.logger.warn('localStorage is not available');
      return;
    }
    
    const items: Record<string, string> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        items[key] = localStorage.getItem(key) || '';
      }
    }
    
    this.logger.debug('localStorage contents:', items);
    
    if (typeof window !== 'undefined' && typeof window.console !== 'undefined') {
      console.groupCollapsed('%cLocalStorage Contents', 'color: purple; font-weight: bold;');
      console.table(Object.keys(items).map(key => ({
        key,
        size: items[key].length,
        preview: items[key].substring(0, 50) + (items[key].length > 50 ? '...' : '')
      })));
      console.groupEnd();
    }
  }
}
```

## 移行ガイドライン

### 1. ブラウザ環境への移行

フェーズ1で実施した抽象化により、ほとんどのコードはそのままブラウザで動作するはずです。ただし、以下のポイントに注意して移行を進めてください。

#### 1.1 インフラ層の初期化

ブラウザ環境では、アプリケーションの起動時に適切なインフラ層を初期化する必要があります。以下の初期化コードをHTMLファイルのscriptタグ内、またはエントリポイントのJavaScriptファイルの先頭に配置します。

```html
<script type="module">
  import { InfrastructureProvider, Runtime } from './infrastructure/providers/InfrastructureProvider.js';
  
  // ブラウザ環境向けに初期化
  InfrastructureProvider.initialize({
    runtime: Runtime.BROWSER,
    browserOptions: {
      baseUrl: '/schemas/',
      enableCaching: true
    }
  });
</script>
```
#### 1.2 スキーマファイルのデプロイ

ブラウザからアクセスできるようにスキーマファイルをデプロイする必要があります：

1. 静的ファイルとしてスキーマファイルをデプロイする
   ```bash
   # JSONスキーマファイルを配置するディレクトリを作成
   mkdir -p public/schemas
   
   # Function__Meta.jsonとすべての関連スキーマをコピー
   cp /path/to/Function__Meta.json public/schemas/
   cp /path/to/*__Function.json public/schemas/
   ```

2. フロントエンドビルドプロセスに組み込む
   ```javascript
   // webpack.config.js
   module.exports = {
     // ...
     plugins: [
       new CopyWebpackPlugin({
         patterns: [
           { from: 'schemas', to: 'schemas' }
         ]
       })
     ]
   };
   ```

#### 1.3 環境依存の処理

環境に応じた条件分岐が必要な場合は、以下のようにInfrastructureProviderの環境チェック関数を利用してください：

```typescript
import { isBrowser, isDeno } from '../infrastructure/providers/InfrastructureProvider.ts';

// 環境依存の処理
if (isBrowser()) {
  // ブラウザ特有の処理
} else if (isDeno()) {
  // Deno特有の処理
} else {
  // その他の環境の処理
}
```

### 2. モジュールバンドリング

ブラウザでの動作が特に必要な場合は、モジュールバンドラー（例：Webpack、Rollup、esbuild）を使用して必要なモジュールをバンドルすることを検討してください。

```bash
# esbuildを使った簡単なバンドル例
esbuild browser/index.ts --bundle --outfile=public/js/functional-schema.js
```

## パフォーマンス最適化

### 1. ブラウザキャッシュの活用

特に大きなスキーマファイルを扱う場合は、ブラウザのキャッシュ機能を活用してパフォーマンスを向上させることができます：

1. Service Workerを使用したキャッシュ
   ```javascript
   // service-worker.js
   self.addEventListener('install', (event) => {
     event.waitUntil(
       caches.open('schema-cache-v1').then((cache) => {
         return cache.addAll([
           '/schemas/Function__Meta.json',
           // その他のスキーマファイル
         ]);
       })
     );
   });
   ```

2. IndexedDBを使用した永続化
   ```javascript
   // 大きなJSONスキーマをIndexedDBに保存する例
   async function saveSchemaToIndexedDB(schema, key) {
     const db = await openDatabase();
     const tx = db.transaction('schemas', 'readwrite');
     const store = tx.objectStore('schemas');
     store.put(schema, key);
     await tx.complete;
   }
   ```
## 検証チェックリスト

ブラウザ環境での動作確認時には、以下の項目を確認してください：

1. **基本機能**
   - [ ] Function__Meta.jsonが正しく読み込まれるか
   - [ ] スキーマリポジトリの読み込み・保存機能が動作するか
   - [ ] URIの正規化が適切に行われるか

2. **パフォーマンス**
   - [ ] 大きなスキーマファイルの読み込みが十分な速度で行われるか
   - [ ] メモリ使用量が許容範囲内か

3. **互換性**
   - [ ] 主要ブラウザ（Chrome、Firefox、Edge、Safari）で動作するか
   - [ ] モバイルブラウザでも問題なく動作するか

4. **エラーハンドリング**
   - [ ] ネットワークエラー時に適切にフォールバックするか
   - [ ] ユーザーにわかりやすいエラーメッセージが表示されるか

## 次のステップ

フェーズ2が完了したら、以下の高度な機能の実装を検討してください：

1. **オフライン対応**
   - Service Workerを使用したオフライン動作のサポート
   - IndexedDBを使用した大規模データの管理

2. **WebAssembly統合**
   - パフォーマンスクリティカルな部分をRustやC++で実装し、WebAssemblyとして利用

3. **プログレッシブWebアプリ化**
   - インストール可能なPWAとしての機能提供
   - プッシュ通知などの高度な機能の統合

## まとめ

フェーズ2の実装により、関数型スキーマ生成処理がブラウザ環境でも動作可能になりました。インフラ層の抽象化と環境検出メカニズムにより、同じコードベースをDeno環境とブラウザ環境の両方で使用できるようになりました。

これにより、ユーザーはローカル環境でスキーマを生成・編集するだけでなく、Webブラウザを通じてどこからでもスキーマを参照・編集できるようになります。また、インフラ層のアダプターパターンにより、将来的にNode.jsやその他の環境への拡張も容易になります。
