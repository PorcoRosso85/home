#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --no-check
/**
 * generateNew.ts
 * 
 * 拡張可能なスキーマ生成コマンドの実装
 * 型を指定して様々なスキーマを生成します
 */

import { CliCommand } from '../cli.ts';
import { 
  schemaGenerationService,
  SchemaGenerationResult
} from '../../application/schemaGenerationService.ts';
import { 
  SchemaTypeKind,
  SchemaGeneratorOptions,
  FunctionSchemaGeneratorOptions
} from '../../domain/generators/index.ts';
import { createSchemaRepository, RepositoryType } from '../../infrastructure/repositoryFactory.ts';
import { buildFeaturesFromConfig } from '../../application/genSchema.ts';

/**
 * 生成コマンドの設定オプション
 */
interface GenerateCommandOptions {
  // 基本オプション
  typeName: string;
  typeKind: SchemaTypeKind;
  outputPath: string;
  title: string;
  description: string;
  version: string;
  resourceUri: string;
  
  // 表示オプション
  verbose: boolean;
  dryRun: boolean;
  
  // 機能オプション
  multipleReturns: boolean;
  composition: boolean;
  
  // ストレージオプション
  useDb: boolean;
  dbType: string;
  
  // スキッププロパティ
  skipProperties: string[];
}

/**
 * デフォルトの設定値
 */
const defaultOptions: GenerateCommandOptions = {
  typeName: 'function',
  typeKind: SchemaTypeKind.FUNCTION,
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
  skipProperties: []
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
    
    if (arg === '--type' || arg === '-t') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.typeName = nextArg.toLowerCase();
        // typeKindを設定
        switch (nextArg.toLowerCase()) {
          case 'function':
            options.typeKind = SchemaTypeKind.FUNCTION;
            break;
          case 'struct':
            options.typeKind = SchemaTypeKind.STRUCT;
            break;
          case 'list':
            options.typeKind = SchemaTypeKind.LIST;
            break;
          case 'enum':
            options.typeKind = SchemaTypeKind.ENUM;
            break;
          case 'union':
            options.typeKind = SchemaTypeKind.UNION;
            break;
          case 'primitive':
            options.typeKind = SchemaTypeKind.PRIMITIVE;
            break;
          default:
            console.warn(`警告: 未知の型 '${nextArg}'。デフォルトの 'function' を使用します。`);
            options.typeName = 'function';
            options.typeKind = SchemaTypeKind.FUNCTION;
        }
        i++;
      }
    } else if (arg === '--output' || arg === '-o') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.outputPath = nextArg;
        i++;
      }
    } else if (arg === '--title') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.title = nextArg;
        i++;
      }
    } else if (arg === '--desc' || arg === '--description' || arg === '-d') {
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
    // --no-xxx形式のフラグは廃止され、--skipフラグに統一されました
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
    } else if (arg === '--skip') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.skipProperties = nextArg.split(',');
        
        // 特定の機能フラグの処理
        if (options.skipProperties.includes('multipleReturns')) {
          options.multipleReturns = false;
        }
        if (options.skipProperties.includes('composition')) {
          options.composition = false;
        }
        
        i++;
      }
    }
  }
  
  return options;
}

/**
 * 拡張スキーマ生成コマンドの実装
 */
export const command: CliCommand = {
  name: "generate-new",
  aliases: ["gen-new", "gn"],
  description: "拡張可能なスキーマ生成機能を使って型スキーマを生成します",
  
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
      const repository = options.dryRun ? undefined : createSchemaRepository({
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
      
      // 共通の生成オプションを構築
      const genOptions: SchemaGeneratorOptions = {
        title: options.title,
        description: options.description,
        version: options.version,
        resourceUri: options.resourceUri
      };
      
      // 型に応じた処理
      let result: SchemaGenerationResult;

      // 関数型の場合は特別な処理
      if (options.typeKind === SchemaTypeKind.FUNCTION) {
        // 関数型固有のオプションを構築
        const functionOptions: FunctionSchemaGeneratorOptions = {
          ...genOptions,
          features: buildFeaturesFromConfig({
            outputPath: options.outputPath,
            title: options.title,
            description: options.description,
            version: options.version,
            resourceUri: options.resourceUri,
            skipProperties: options.skipProperties,
            storageType: repositoryType,
            dbConfig: options.useDb ? { type: options.dbType } : undefined,
            enableFeatures: {
              purity: true,
              evaluation: true,
              currying: true,
              recursion: true,
              memoization: true,
              async: true,
              parallel: false,
              multipleReturns: options.multipleReturns,
              composition: options.composition
            }
          })
        };

        // 関数スキーマを生成
        let schema = schemaGenerationService.generateFunctionSchema(functionOptions);

        // スキップするプロパティがある場合は削除
        if (options.skipProperties.length > 0) {
          schema = schemaGenerationService.removeSchemaProperties(schema, options.skipProperties);
        }

        // ドライランの場合はスキーマのみ返し、そうでなければ保存も実行
        if (options.dryRun) {
          result = {
            success: true,
            message: 'スキーマが正常に生成されましたが、ドライランモードのため保存されていません',
            schema
          };
        } else {
          result = await schemaGenerationService.saveGeneratedSchema(
            schema, 
            options.outputPath,
            repository
          );
        }
      } else {
        // その他の型の場合は共通処理
        if (options.dryRun) {
          // ドライラン時はスキーマのみを生成
          const schema = schemaGenerationService.generateSchemaByTypeName(
            options.typeName, 
            genOptions
          );
          
          result = {
            success: true,
            message: 'スキーマが正常に生成されましたが、ドライランモードのため保存されていません',
            schema
          };
        } else {
          // 通常実行時は生成と保存を実行
          result = await schemaGenerationService.generateAndSaveSchema(
            options.typeName,
            genOptions,
            undefined, // メタデータはここでは指定しない
            options.skipProperties,
            options.outputPath,
            repository
          );
        }
      }
      
      // 結果を表示
      if (options.dryRun) {
        console.log("生成されたスキーマのプレビュー:");
        if (options.verbose) {
          console.log(JSON.stringify(result.schema, null, 2));
        } else {
          console.log("(スキーマのプレビューは省略されました。--verbose フラグで表示)");
        }
        console.log("\nスキーマのドライラン生成が完了しました");
      } else if (result.success) {
        console.log(`✅ ${result.message}`);
        
        if (options.useDb) {
          console.log(`スキーマはデータベース(${options.dbType})に保存されました`);
        } else {
          console.log(`スキーマはファイルに保存されました: ${options.outputPath}`);
        }
      } else {
        console.error(`❌ ${result.message}`);
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
    console.log("使用方法: cli.ts generate-new [オプション]");
    console.log("");
    console.log("説明:");
    console.log("  拡張可能なスキーマ生成機能を使って様々な型スキーマを生成します。");
    console.log("");
    console.log("オプション:");
    console.log("  --type, -t <型名>         生成するスキーマの型");
    console.log("                           (function, struct, list, enum, union, primitive)");
    console.log("                           デフォルト: function");
    console.log("  --output, -o <パス>       出力ファイルパス");
    console.log("                           デフォルト: ./Function__Meta.json");
    console.log("  --title <タイトル>        スキーマのタイトル");
    console.log("  --desc, --description, -d <説明> スキーマの説明");
    console.log("  --version, -v <バージョン> スキーマのバージョン");
    console.log("  --resource-uri <URI>      リソースURIのベースパス");
    console.log("  --verbose                 詳細出力モード");
    console.log("  --dry-run                 ファイルを保存せずに実行");
    console.log("  --skip <prop1,prop2,...>  スキップするプロパティ（カンマ区切り）");
    console.log("                           例: composition,tests,multipleReturns,thrownExceptions");
    console.log("                           有効な値: features,composition,tests,multipleReturns,");
    console.log("                                     thrownExceptions,usageExamples,externalDependencies等");
    console.log("");
    console.log("ストレージオプション:");
    console.log("  --db                      データベースを使用してスキーマを保存");
    console.log("  --db-type <タイプ>         データベースタイプを指定（cozo, inmemory など）");
    console.log("                           --db フラグが指定された場合のデフォルト: inmemory");
    console.log("");
    console.log("例:");
    console.log("  cli.ts generate-new");
    console.log("  cli.ts generate-new --type function --output ./custom-schema.json");
    console.log("  cli.ts generate-new -t struct --title \"構造体スキーマ\" -d \"説明文\"");
    console.log("  cli.ts generate-new --skip composition,tests,multipleReturns");
    console.log("  cli.ts generate-new --skip features");
    console.log("  cli.ts generate-new --db");
    console.log("  cli.ts generate-new --db-type cozo");
  }
};
