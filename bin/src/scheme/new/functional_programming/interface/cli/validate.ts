#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --allow-env --no-check
/**
 * validate.ts
 * 
 * スキーマとURI検証コマンドの実装
 * スキーマの検証とURIの正規化を行います
 */

import * as path from 'node:path';
import { CliCommand } from '../cli.ts';
import { SchemaValidator } from '../../domain/validators/SchemaValidator.ts';
import { UriHandlingService } from '../../application/UriHandlingService.ts';
import { ResourceUri } from '../../domain/valueObjects/ResourceUri.ts';

/**
 * 検証コマンドの設定オプション
 */
interface ValidateCommandOptions {
  filePath: string;
  uriToValidate?: string;
  normalizeUris: boolean;
  allowRelativePaths: boolean;
  verbose: boolean;
  fixIssues: boolean;
}

/**
 * デフォルトの設定値
 */
const defaultOptions: ValidateCommandOptions = {
  filePath: './Function__Meta.json',
  normalizeUris: true,
  allowRelativePaths: false,
  verbose: false,
  fixIssues: false,
};

/**
 * コマンドライン引数をパースする
 * @param args コマンドライン引数
 * @returns パースされた設定オプション
 */
function parseArgs(args: string[]): ValidateCommandOptions {
  const options = { ...defaultOptions };
  
  // 最初の引数がオプションでなければファイルパスとみなす
  if (args.length > 0 && !args[0].startsWith('-')) {
    options.filePath = args[0];
  }
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--uri') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.uriToValidate = nextArg;
        i++;
      }
    } else if (arg === '--allow-relative') {
      options.allowRelativePaths = true;
    } else if (arg === '--no-normalize') {
      options.normalizeUris = false;
    } else if (arg === '--verbose') {
      options.verbose = true;
    } else if (arg === '--fix') {
      options.fixIssues = true;
    }
  }
  
  return options;
}

/**
 * 検証コマンドの実装
 */
export const command: CliCommand = {
  name: "validate",
  aliases: ["val", "check"],
  description: "スキーマの検証とURIの正規化を行います",
  
  /**
   * 検証コマンドを実行する
   * @param args 引数配列
   */
  async execute(args: string[]): Promise<void> {
    try {
      // 引数をパース
      const options = parseArgs(args);
      
      // 詳細モードのログ出力
      if (options.verbose) {
        console.log("検証設定:");
        console.log(JSON.stringify(options, null, 2));
      }
      
      // URIを直接検証する場合
      if (options.uriToValidate) {
        const uriService = new UriHandlingService();
        
        try {
          const result = uriService.normalizeUri(options.uriToValidate, {
            allowRelative: options.allowRelativePaths
          });
          
          console.log(`URI検証結果: ${options.uriToValidate}`);
          console.log(`正規化されたURI: ${result}`);
          console.log(`✅ URIは有効です`);
        } catch (error) {
          if (error instanceof Error) {
            console.error(`❌ URI検証エラー: ${error.message}`);
          } else {
            console.error(`❌ URI検証中に不明なエラーが発生しました`);
          }
        }
        
        return;
      }
      
      // スキーマファイルパスの解決
      const filePath = path.isAbsolute(options.filePath)
        ? options.filePath
        : path.resolve(Deno.cwd(), options.filePath);
      
      console.log(`🔍 スキーマを検証中: ${filePath}`);
      
      // スキーマの検証
      const validator = new SchemaValidator();
      
      // スキーマの検証を実行し、結果を取得
      const validationResult = await validator.validateSchema(filePath, {
        normalizeUris: options.normalizeUris,
        allowRelativePaths: options.allowRelativePaths
      });
      
      if (options.verbose) {
        console.log("検証結果:", JSON.stringify(validationResult, null, 2));
      }
      
      // 検証結果の表示
      if (validationResult.isValid) {
        console.log("✅ スキーマは有効です");
        
        if (validationResult.warnings.length > 0) {
          console.log("\n⚠️ 警告:");
          validationResult.warnings.forEach(warning => {
            console.log(`  - ${warning}`);
          });
        }
      } else {
        console.error("❌ スキーマにエラーがあります:");
        validationResult.errors.forEach(error => {
          console.error(`  - ${error}`);
        });
        
        // 問題を修正する場合
        if (options.fixIssues && validationResult.fixableIssues) {
          console.log("\n🔧 修正可能な問題を修正しています...");
          const fixResult = await validator.fixSchemaIssues(filePath, validationResult.fixableIssues);
          
          if (fixResult.success) {
            console.log(`✅ 問題を修正してスキーマを保存しました: ${fixResult.outputPath}`);
          } else {
            console.error(`❌ 問題の修正に失敗しました: ${fixResult.message}`);
          }
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        console.error(`検証中にエラーが発生しました: ${error.message}`);
      } else {
        console.error("検証中に不明なエラーが発生しました");
      }
      throw error;
    }
  },
  
  /**
   * ヘルプ情報を表示する
   */
  showHelp(): void {
    console.log("使用方法: cli.ts validate [ファイルパス] [オプション]");
    console.log("       cli.ts validate --uri <URI>");
    console.log("");
    console.log("説明:");
    console.log("  スキーマファイルの検証とURIの正規化を行います。");
    console.log("");
    console.log("引数:");
    console.log("  [ファイルパス]  検証対象のスキーマファイルパス");
    console.log("                 デフォルト: ./Function__Meta.json");
    console.log("");
    console.log("オプション:");
    console.log("  --uri <URI>        検証するURIを直接指定");
    console.log("  --allow-relative   相対パスを許可する");
    console.log("  --no-normalize     URIの正規化を行わない");
    console.log("  --fix              修正可能な問題を自動修正する");
    console.log("  --verbose          詳細出力モード");
    console.log("");
    console.log("例:");
    console.log("  cli.ts validate");
    console.log("  cli.ts validate ./カスタムスキーマ.json");
    console.log("  cli.ts validate --uri file:///path/to/file.ts");
    console.log("  cli.ts validate --fix");
  }
};

// in-sourceテスト
if (import.meta.main) {
  console.log("検証コマンドのテストを実行中...");
  try {
    await command.execute(["--verbose", "--uri", "file:///example/path.ts"]);
    console.log("\nテスト完了!");
  } catch (error) {
    console.error("テスト実行中にエラーが発生しました:", error);
  }
}
