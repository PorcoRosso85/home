#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --no-check
/**
 * generate.ts
 * 
 * スキーマ生成コマンドの実装
 * 関数型スキーマを生成します
 */

import { CliCommand } from '../cli.ts';
import { schemaGenerationService } from '../../application/genSchema.ts';
import { createSchemaRepository, RepositoryType } from '../../infrastructure/repositoryFactory.ts';

/**
 * 生成コマンドの設定オプション
 */
interface GenerateCommandOptions {
  outputPath: string;
  title: string;
  description: string;
  version: string;
  resourceUri: string;
  verbose: boolean;
  dryRun: boolean;
  multipleReturns: boolean;
  composition: boolean;
  // ストレージオプション
  useDb: boolean;
  dbType: string;
  // 必要に応じて追加のオプション
}

/**
 * デフォルトの設定値
 */
const defaultOptions: GenerateCommandOptions = {
  outputPath: './Function__Meta.json',
  title: 'Function Metadata Schema',
  description: '関数メタデータのスキーマ定義',
  version: '1.0.0',
  resourceUri: 'file://',
  verbose: false,
  dryRun: false,
  multipleReturns: true,
  composition: true,
  // デフォルトはファイルストレージ
  useDb: false,
  dbType: 'inmemory',
};

/**
 * コマンドライン引数をパースする
 * @param args コマンドライン引数
 * @returns パースされた設定オプション
 */
function parseArgs(args: string[]): GenerateCommandOptions {
  const options = { ...defaultOptions };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--output' || arg === '-o') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.outputPath = nextArg;
        i++;
      }
    } else if (arg === '--title' || arg === '-t') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.title = nextArg;
        i++;
      }
    } else if (arg === '--desc' || arg === '-d') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.description = nextArg;
        i++;
      }
    } else if (arg === '--version' || arg === '-v') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.version = nextArg;
        i++;
      }
    } else if (arg === '--resource-uri') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.resourceUri = nextArg;
        i++;
      }
    } else if (arg === '--verbose') {
      options.verbose = true;
    } else if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--no-multiple-returns') {
      options.multipleReturns = false;
    } else if (arg === '--no-composition') {
      options.composition = false;
    } else if (arg === '--db') {
      // DBストレージを使用する
      options.useDb = true;
      // デフォルトのタイプはinmemory
    } else if (arg === '--db-type') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.dbType = nextArg;
        options.useDb = true;  // DB設定があればDBを使用
        i++;
      }
    }
  }
  
  return options;
}

/**
 * 生成コマンドの実装
 */
export const command: CliCommand = {
  name: "generate",
  aliases: ["gen", "g"],
  description: "関数型スキーマを生成します",
  
  /**
   * 生成コマンドを実行する
   * @param args 引数配列
   */
  async execute(args: string[]): Promise<void> {
    try {
      // 引数をパース
      const options = parseArgs(args);
      
      // 詳細モードのログ出力
      if (options.verbose) {
        console.log("スキーマ生成設定:");
        console.log(JSON.stringify(options, null, 2));
      }
      
      // ドライラン処理
      if (options.dryRun) {
        console.log("ドライランモード - スキーマを生成しますが、保存しません");
      }
      
      // リポジトリタイプを決定
      const repositoryType = options.useDb ? RepositoryType.DB : RepositoryType.FILE;
      
      // 適切なリポジトリを作成
      const repository = createSchemaRepository({
        type: repositoryType,
        basePath: '.',
        dbConfig: options.useDb ? { type: options.dbType } : undefined
      });
      
      // ストレージ情報を表示
      if (options.verbose) {
        console.log(`ストレージタイプ: ${repositoryType}`);
        if (options.useDb) {
          console.log(`DBタイプ: ${options.dbType}`);
        }
      }
      
      // スキーマ生成サービスを呼び出す
      const result = await schemaGenerationService.generateSchema({
        outputPath: options.outputPath,
        title: options.title,
        description: options.description,
        version: options.version,
        resourceUri: options.resourceUri,
        skipProperties: [],
        enableFeatures: {
          purity: true,
          evaluation: true,
          currying: true,
          recursion: true,
          memoization: true,
          async: true,
          multipleReturns: options.multipleReturns,
          composition: options.composition,
          parallel: options.verbose
        }
      }, undefined, repository);
      
      // 結果を表示
      if (options.dryRun) {
        console.log("生成されたスキーマのプレビュー:");
        console.log("(スキーマのプレビューは省略されました)");
        console.log("\nスキーマのドライラン生成が完了しました");
      } else if (result.success) {
        console.log(`✅ ${result.message}`);
        
        if (options.useDb) {
          console.log(`スキーマはデータベース(${options.dbType})に保存されました`);
        } else {
          console.log(`スキーマはファイルに保存されました: ${options.outputPath}`);
        }
      }
    } catch (error) {
      console.error(`スキーマ生成中にエラーが発生しました:`, error);
      throw error;
    }
  },
  
  /**
   * ヘルプ情報を表示する
   */
  showHelp(): void {
    console.log("使用方法: cli.ts generate [オプション]");
    console.log("");
    console.log("説明:");
    console.log("  関数型スキーマを生成し、指定されたファイルまたはデータベースに保存します。");
    console.log("");
    console.log("オプション:");
    console.log("  --output, -o <パス>     出力ファイルパス");
    console.log("                         デフォルト: ./Function__Meta.json");
    console.log("  --title, -t <タイトル>   スキーマのタイトル");
    console.log("  --desc, -d <説明>       スキーマの説明");
    console.log("  --version, -v <バージョン> スキーマのバージョン");
    console.log("  --resource-uri <URI>    リソースURIのベースパス");
    console.log("  --verbose               詳細出力モード");
    console.log("  --dry-run               ファイルを保存せずに実行");
    console.log("  --no-multiple-returns    複数戻り値機能を無効化");
    console.log("  --no-composition         関数合成機能を無効化");
    console.log("");
    console.log("ストレージオプション:");
    console.log("  --db                    データベースを使用してスキーマを保存");
    console.log("  --db-type <タイプ>       データベースタイプを指定（cozo, inmemory など）");
    console.log("                         --db フラグが指定された場合のデフォルト: inmemory");
    console.log("");
    console.log("例:");
    console.log("  cli.ts generate");
    console.log("  cli.ts generate --output ./custom-schema.json");
    console.log("  cli.ts generate -t \"カスタムスキーマ\" -d \"説明文\"");
    console.log("  cli.ts generate --db");
    console.log("  cli.ts generate --db-type cozo");
  }
};
