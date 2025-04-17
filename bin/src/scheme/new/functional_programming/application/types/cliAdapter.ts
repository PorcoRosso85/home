/**
 * cliAdapter.ts
 * 
 * CLIインターフェースのためのアダプター
 * コマンドライン引数をドメインオブジェクトに変換します
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { CommandArgs, SchemaDataAccess, parseFunctionSchema } from '../type.ts';
import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * CLIデータアクセスアダプター
 * CLI環境でのファイルシステムを使用したデータアクセスを実装
 */
export class CliSchemaDataAccess implements SchemaDataAccess {
  /**
   * スキーマをロードする
   * 
   * @param path ファイルパス
   * @returns ロードされたスキーマ
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    try {
      const fileContent = await Deno.readTextFile(path);
      return parseFunctionSchema(fileContent);
    } catch (error) {
      throw new Error(`スキーマファイルの読み込みに失敗しました: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * スキーマをファイルに保存する
   * 
   * @param schema 保存するスキーマ
   * @param path 保存先パス
   */
  async saveSchema(schema: FunctionSchema, path: string): Promise<void> {
    try {
      const dirPath = path.substring(0, path.lastIndexOf('/'));
      try {
        await Deno.mkdir(dirPath, { recursive: true });
      } catch (e) {
        // ディレクトリが既に存在する場合は無視
      }
      
      await Deno.writeTextFile(path, JSON.stringify(schema, null, 2));
    } catch (error) {
      throw new Error(`スキーマファイルの保存に失敗しました: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 依存関係グラフを取得する
   * 
   * @param rootSchemaPath ルートスキーマのパス
   * @returns 依存関係グラフ
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    // この実装はドメイン層のサービスに委譲することが想定される
    // または、適切な実装を追加する
    throw new Error("この機能はまだ実装されていません");
  }

  /**
   * スキーマを検証する
   * 
   * @param schema 検証するスキーマ
   * @returns 検証結果 (true: 有効, false: 無効)
   */
  async validateSchema(schema: FunctionSchema): Promise<boolean> {
    // この実装はドメイン層のバリデーションサービスに委譲することが想定される
    return true;
  }
}

/**
 * CLIコマンド引数からCommandArgs型へ変換する関数
 * 
 * @param args コマンドライン引数
 * @returns CommandArgs オブジェクト
 */
export function parseCLIArgs(args: string[]): CommandArgs {
  const result: CommandArgs = {
    command: '',
    flags: {},
    options: {},
    args: []
  };

  if (args.length > 0) {
    result.command = args[0];
  }

  for (let i = 1; i < args.length; i++) {
    const arg = args[i];

    if (arg.startsWith('--')) {
      if (arg.includes('=')) {
        // --key=value
        const [key, value] = arg.substring(2).split('=', 2);
        result.options[key] = value;
      } else {
        // --flag
        result.flags[arg.substring(2)] = true;
      }
    } else if (arg.startsWith('-')) {
      // -f
      result.flags[arg.substring(1)] = true;
    } else if (i > 0 && args[i-1] === '-o') {
      // -o output.json
      result.output = arg;
    } else if (!result.input && (arg.endsWith('.json') || arg.endsWith('.ts'))) {
      // input.json
      result.input = arg;
    } else {
      // その他の引数
      result.args.push(arg);
    }
  }

  return result;
}
