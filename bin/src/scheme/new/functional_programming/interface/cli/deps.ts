#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --check
/**
 * deps.ts
 * 
 * 依存関係表示コマンドの実装
 * スキーマの依存関係を解析して表示します
 */

import * as path from 'node:path';
import { CliCommand } from '../cli.ts';
import { analyzeDependencies, formatDependencyAnalysisResult } from "../../application/commands/depsAnalyzer.ts";
import { dependencyTreeToGraph } from "../../domain/service/graphBuilder.ts";
import { 
  serializeToJson, 
  convertToDot, 
  convertToMermaid, 
  convertToText,
  convertToCsv
} from "../../application/serializers/graphSerializer.ts";

/**
 * 依存関係コマンドの設定オプション
 */
interface DepsCommandOptions {
  schemaPath: string;
  format: "tree" | "graph" | "json" | "dot" | "mermaid" | "csv" | "text";
  outputPath?: string;
  verbose: boolean;
  maxDepth?: number;
}

/**
 * デフォルトの設定値
 */
const defaultOptions: DepsCommandOptions = {
  schemaPath: './Function__Meta.json',
  format: 'tree',
  verbose: false,
};

/**
 * コマンドライン引数をパースする
 * @param args コマンドライン引数
 * @returns パースされた設定オプション
 */
function parseArgs(args: string[]): DepsCommandOptions {
  const options = { ...defaultOptions };
  
  // 最初の引数がオプションでなければスキーマパスとみなす
  if (args.length > 0 && !args[0].startsWith('-')) {
    options.schemaPath = args[0];
  }
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--format' || arg === '-f') {
      if (nextArg && !nextArg.startsWith('-')) {
        const format = nextArg.toLowerCase();
        if (['tree', 'graph', 'json', 'dot', 'mermaid', 'csv', 'text'].includes(format)) {
          options.format = format as any;
        } else {
          console.warn(`警告: 不明な形式 '${format}' が指定されました。デフォルトの 'tree' を使用します。`);
        }
        i++;
      }
    } else if (arg === '--output' || arg === '-o') {
      if (nextArg && !nextArg.startsWith('-')) {
        options.outputPath = nextArg;
        i++;
      }
    } else if (arg === '--verbose') {
      options.verbose = true;
    } else if (arg === '--max-depth') {
      if (nextArg && !nextArg.startsWith('-')) {
        const depth = parseInt(nextArg, 10);
        if (!isNaN(depth) && depth > 0) {
          options.maxDepth = depth;
        } else {
          console.warn("警告: 無効な深さが指定されました。制限なしで実行します。");
        }
        i++;
      }
    }
  }
  
  return options;
}

/**
 * 依存関係コマンドの実装
 */
export const command: CliCommand = {
  name: "deps",
  aliases: ["dependencies", "dep"],
  description: "スキーマの依存関係を解析して表示します",
  
  /**
   * 依存関係コマンドを実行する
   * @param args 引数配列
   */
  async execute(args: string[]): Promise<void> {
    try {
      // 引数をパース
      const options = parseArgs(args);
      
      // 詳細モードのログ出力
      if (options.verbose) {
        console.log("依存関係解析設定:");
        console.log(JSON.stringify(options, null, 2));
      }
      
      // スキーマパスの解決
      const schemaPath = path.isAbsolute(options.schemaPath)
        ? options.schemaPath
        : path.resolve(Deno.cwd(), options.schemaPath);
      
      console.log(`📊 依存関係を解析中: ${schemaPath}`);
      
      // 依存関係の解析
      const result = await analyzeDependencies(schemaPath);
      
      // グラフ変換 (正しく dependencyTree プロパティを使用)
      if (!result.success || !result.dependencyTree) {
        throw new Error(`依存関係の解析に失敗しました: ${result.message}`);
      }
      
      const graph = dependencyTreeToGraph(result.dependencyTree);
      
      // 出力形式に応じた処理
      let output: string;
      
      switch (options.format) {
        case 'json':
          output = serializeToJson(graph);
          break;
        case 'dot':
          output = convertToDot(graph);
          break;
        case 'mermaid':
          output = convertToMermaid(graph);
          break;
        case 'csv':
          output = convertToCsv(graph);
          break;
        case 'text':
          output = convertToText(graph);
          break;
        case 'tree':
        case 'graph':
        default:
          output = formatDependencyAnalysisResult(result, options.format, options.maxDepth);
          break;
      }
      
      // 出力処理
      if (options.outputPath) {
        const outputPath = path.isAbsolute(options.outputPath)
          ? options.outputPath
          : path.resolve(Deno.cwd(), options.outputPath);
        
        await Deno.writeTextFile(outputPath, output);
        console.log(`✅ 依存関係解析結果を保存しました: ${outputPath}`);
      } else {
        // 標準出力に表示
        console.log("\n依存関係解析結果:");
        console.log(output);
      }
    } catch (error) {
      if (error instanceof Error) {
        console.error(`依存関係解析中にエラーが発生しました: ${error.message}`);
      } else {
        console.error("依存関係解析中に不明なエラーが発生しました");
      }
      throw error;
    }
  },
  
  /**
   * ヘルプ情報を表示する
   */
  showHelp(): void {
    console.log("使用方法: cli.ts deps [スキーマパス] [オプション]");
    console.log("");
    console.log("説明:");
    console.log("  スキーマファイルの依存関係を解析して表示します。");
    console.log("");
    console.log("引数:");
    console.log("  [スキーマパス]  解析対象のスキーマファイルパス");
    console.log("                 デフォルト: ./Function__Meta.json");
    console.log("");
    console.log("オプション:");
    console.log("  --format, -f <形式>  出力形式");
    console.log("                      tree, graph, json, dot, mermaid, csv, text");
    console.log("                      デフォルト: tree");
    console.log("  --output, -o <パス>  出力ファイルパス");
    console.log("                      指定しない場合は標準出力に表示");
    console.log("  --max-depth <数値>   表示する依存関係の最大深さ");
    console.log("  --verbose           詳細出力モード");
    console.log("");
    console.log("例:");
    console.log("  cli.ts deps");
    console.log("  cli.ts deps ./カスタムスキーマ.json");
    console.log("  cli.ts deps --format mermaid --output deps.mmd");
    console.log("  cli.ts deps --max-depth 3");
  }
};

// in-sourceテスト
if (import.meta.main) {
  console.log("依存関係コマンドのテストを実行中...");
  await command.execute(["--format", "text", "--verbose"]);
  console.log("\nテスト完了!");
}
