#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --no-check

// cli.ts - コマンドラインインターフェースの実装

import { 
  extractDependencies, 
  extractAllDependencies,
  DEFAULT_SCHEMA_EXTENSIONS,
  DEFAULT_EXCLUDE_PATTERNS,
  DEFAULT_REF_KEYWORDS
} from './core/parser/schemaParser.ts';

import {
  formatWithRelativePaths,
  formatAsJson,
  formatAsText,
  formatAsDot
} from './core/formatter/dependencyFormatter.ts';

import {
  printToConsole,
  printError,
  printInfo,
  printDebug,
  printSuccess
} from './core/output/outputHandler.ts';

import { outputBasicFormat, outputTreeFormat, outputHtmlFormat, outputMarkdownFormat } from './core/output/outputFormatters.ts';

import { denoFileSystem } from './platform/deno/fileSystem.ts';
import { denoPathUtils } from './platform/deno/pathUtils.ts';
import { SchemaConfig } from './core/types.ts';

// 既定の設定
const DEFAULT_CONFIG: SchemaConfig = {
  baseDir: '/home/nixos/scheme/new/ref',
  rootSchema: 'RequirementsDefinition.json',
  recursiveSearch: true,
  useRelativePaths: true,
  debug: false
};

// 出力形式の種類
type OutputFormat = 'json' | 'text' | 'dot' | 'tree' | 'html' | 'markdown';

/**
 * コマンドライン引数を解析して設定をマージする
 */
function parseConfig(): SchemaConfig & { format: OutputFormat } {
  const args = Deno.args;
  const cliConfig: Partial<SchemaConfig> & { format?: OutputFormat } = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--base-dir' || arg === '-d') {
      cliConfig.baseDir = args[++i];
    } else if (arg === '--root-schema' || arg === '-r') {
      cliConfig.rootSchema = args[++i];
    } else if (arg === '--recursive' || arg === '-R') {
      cliConfig.recursiveSearch = true;
    } else if (arg === '--no-recursive') {
      cliConfig.recursiveSearch = false;
    } else if (arg === '--relative-paths') {
      cliConfig.useRelativePaths = true;
    } else if (arg === '--absolute-paths') {
      cliConfig.useRelativePaths = false;
    } else if (arg === '--format' || arg === '-f') {
      const format = args[++i];
      if (format === 'json' || format === 'text' || format === 'dot' || format === 'tree' || format === 'html' || format === 'markdown') {
        cliConfig.format = format;
      } else {
        printError(`不明な出力形式: ${format}`);
        printHelp();
        Deno.exit(1);
      }
    } else if (arg === '--debug') {
      cliConfig.debug = true;
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      Deno.exit(0);
    } else if (!arg.startsWith('-') && !cliConfig.baseDir) {
      // 最初の非オプション引数はベースディレクトリとして扱う
      cliConfig.baseDir = arg;
    }
  }
  
  // 設定をマージして返す
  return {
    ...DEFAULT_CONFIG,
    ...cliConfig,
    format: cliConfig.format || 'json'
  };
}

/**
 * ヘルプメッセージを表示
 */
function printHelp(): void {
  printToConsole(`
JSONスキーマ依存関係解析ツール

使用方法:
  ./cli.ts [options] [base-dir]

オプション:
  -d, --base-dir <dir>    スキーマファイルのベースディレクトリ
  -r, --root-schema <file> ルートスキーマファイルの名前
  -R, --recursive         ディレクトリを再帰的に探索する (デフォルト)
  --no-recursive          再帰探索を無効にする
  --relative-paths        相対パスを使用する (デフォルト)
  --absolute-paths        絶対パスを使用する
  -f, --format <format>   出力形式 (json, text, dot, tree, html, markdown)
  --debug                 デバッグ情報を表示する
  -h, --help              このヘルプメッセージを表示する
`);
}

/**
 * メイン処理
 */
async function main(): Promise<void> {
  try {
    // 設定の解析
    const config = parseConfig();
    
    if (config.debug) {
      printDebug('設定:', true);
      printDebug(JSON.stringify(config, null, 2), true);
    }
    
    // 依存関係の抽出
    let dependencies;
    
    if (config.recursiveSearch) {
      printInfo(`${config.baseDir} 内のすべてのスキーマファイルを探索中...`);
      dependencies = await extractAllDependencies(
        config.baseDir,
        denoFileSystem,
        denoPathUtils,
        DEFAULT_SCHEMA_EXTENSIONS,
        DEFAULT_EXCLUDE_PATTERNS,
        DEFAULT_REF_KEYWORDS,
        config.debug
      );
    } else {
      const rootSchemaPath = denoPathUtils.join(config.baseDir, config.rootSchema);
      
      if (config.debug) {
        printDebug(`ルートスキーマパス: ${rootSchemaPath}`, true);
      }
      
      dependencies = await extractDependencies(
        rootSchemaPath,
        denoFileSystem,
        denoPathUtils,
        config.baseDir,
        DEFAULT_REF_KEYWORDS
      );
    }
    
    // 結果の整形
    let formattedResult;
    let outputDependencies = dependencies;
    
    // 相対パスに変換
    if (config.useRelativePaths) {
      outputDependencies = formatWithRelativePaths(
        dependencies,
        config.baseDir,
        denoPathUtils
      );
    }
    
    // 指定された形式にフォーマット
    switch (config.format) {
      case 'json':
        formattedResult = formatAsJson(outputDependencies);
        break;
      case 'text':
        formattedResult = formatAsText(outputDependencies);
        break;
      case 'dot':
        formattedResult = formatAsDot(outputDependencies);
        break;
      case 'tree':
      case 'html':
      case 'markdown':
        // これらの形式はフォーマット後に直接出力するためここでは何もしない
        formattedResult = '';
        break;
    }
    
    // 出力処理
    switch (config.format) {
      case 'json':
      case 'text':
      case 'dot':
        // 基本フォーマットで出力
        outputBasicFormat(outputDependencies, formattedResult);
        break;
      case 'tree':
        // ツリーフォーマットで出力
        outputTreeFormat(outputDependencies);
        break;
      case 'html':
        // HTMLフォーマットで出力
        outputHtmlFormat(outputDependencies);
        break;
      case 'markdown':
        // マークダウンフォーマットで出力
        await outputMarkdownFormat(outputDependencies, denoFileSystem, config.baseDir);
        break;
    }
    
  } catch (error: any) {
    printError(error.message);
    Deno.exit(1);
  }
}

// メイン処理を実行
if (import.meta.main) {
  main();
}
