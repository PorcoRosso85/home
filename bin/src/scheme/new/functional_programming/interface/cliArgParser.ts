/**
 * cliArgParser.ts
 * 
 * CLIの引数解析モジュール
 */

import { RepositoryType } from '../infrastructure/repositoryFactory.ts';

/**
 * スキーマ生成設定
 */
export interface SchemaGeneratorConfig {
  /** 出力ファイルパス */
  outputPath: string;
  /** タイトル */
  title: string;
  /** 説明 */
  description: string;
  /** バージョン */
  version: string;
  /** リソースURI */
  resourceUri: string;
  /** スキップするプロパティの配列 */
  skipProperties: string[];
  /** ストレージタイプ (FILE, DB, MEMORY) */
  storageType: RepositoryType;
  /** DBの接続情報（DBストレージ使用時） */
  dbConfig?: {
    /** DB種別 (cozo, sqlite, inmemory) */
    type: string;
    /** 接続パス */
    path?: string;
  };
  /** 有効化する機能 */
  enableFeatures: {
    /** 純粋性 */
    purity: boolean;
    /** 評価戦略 */
    evaluation: boolean;
    /** カリー化 */
    currying: boolean;
    /** 再帰 */
    recursion: boolean;
    /** メモ化 */
    memoization: boolean;
    /** 非同期 */
    async: boolean;
    /** 並列処理 */
    parallel: boolean;
    /** 複数戻り値 */
    multipleReturns: boolean;
    /** 関数合成 */
    composition: boolean;
  };
}

/**
 * デフォルトのスキーマ生成設定
 */
export const defaultConfig: SchemaGeneratorConfig = {
  outputPath: './Function__Meta.json',
  title: 'Function Metadata Schema',
  description: '関数メタデータのスキーマ定義',
  version: '1.0.0',
  resourceUri: 'file://',
  skipProperties: [],
  enableFeatures: {
    purity: true,
    evaluation: true,
    currying: true,
    recursion: true,
    memoization: true,
    async: true,
    parallel: false,
    multipleReturns: true,
    composition: true
  }
};

/**
 * コマンドライン引数からスキーマ生成設定を構築
 * 
 * @param args コマンドライン引数
 * @returns スキーマ生成設定
 */
export function parseSchemaGeneratorArgs(args: string[]): SchemaGeneratorConfig {
  const config = { ...defaultConfig };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--output' || arg === '-o') {
      if (nextArg && !nextArg.startsWith('-')) {
        config.outputPath = nextArg;
        i++;
      }
    } else if (arg === '--title' || arg === '-t') {
      if (nextArg && !nextArg.startsWith('-')) {
        config.title = nextArg;
        i++;
      }
    } else if (arg === '--desc' || arg === '-d') {
      if (nextArg && !nextArg.startsWith('-')) {
        config.description = nextArg;
        i++;
      }
    } else if (arg === '--version' || arg === '-v') {
      if (nextArg && !nextArg.startsWith('-')) {
        config.version = nextArg;
        i++;
      }
    } else if (arg === '--resource-uri') {
      if (nextArg && !nextArg.startsWith('-')) {
        config.resourceUri = nextArg;
        i++;
      }
    } else if (arg === '--no-purity') {
      config.enableFeatures.purity = false;
    } else if (arg === '--no-currying') {
      config.enableFeatures.currying = false;
    } else if (arg === '--no-recursion') {
      config.enableFeatures.recursion = false;
    } else if (arg === '--no-memoization') {
      config.enableFeatures.memoization = false;
    } else if (arg === '--no-async') {
      config.enableFeatures.async = false;
    } else if (arg === '--no-multiple-returns') {
      config.enableFeatures.multipleReturns = false;
    } else if (arg === '--no-composition') {
      config.enableFeatures.composition = false;
    } else if (arg === '--parallel') {
      config.enableFeatures.parallel = true;
    }
  }
  
  return config;
}
