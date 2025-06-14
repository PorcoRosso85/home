#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write

/**
 * 要件定義JSONから関数定義JSONを生成するスクリプト
 * 
 * 使用方法:
 *   deno run --allow-read --allow-write requirementsToFunctionUsecase.ts [オプション] <要件ID>
 * 
 * オプション:
 *   --reqDir=<ディレクトリ>   統一要件JSONファイルが格納されているディレクトリ（デフォルト: ./data/requirements）
 *   --outDir=<ディレクトリ>   出力ディレクトリ（デフォルト: ./data/config）
 *   --force                 既存の出力ファイルを上書き
 *   --dryRun                実際に出力せずに内容を表示
 */

import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { join, basename } from "https://deno.land/std@0.220.1/path/mod.ts";

// 関数メタスキーマの参照パス
const FUNCTION_META_SCHEMA_PATH = "../../data/meta/Function.meta.json";

/**
 * メイン関数
 */
async function main() {
  // コマンドライン引数を解析
  const args = parse(Deno.args, {
    string: ["reqDir", "outDir"],
    boolean: ["force", "dryRun"],
    default: {
      reqDir: "./data/requirements",
      outDir: "./data/config",
      force: false,
      dryRun: false
    }
  });

  // 要件IDを取得
  const requirementId = args._[0] as string;
  if (!requirementId) {
    console.error("エラー: 要件IDを指定してください");
    console.log("使用例: deno run --allow-read --allow-write requirementsToFunctionUsecase.ts UserManager");
    Deno.exit(1);
  }

  try {
    // メタスキーマの読み込み
    const functionMetaSchema = await loadFunctionMetaSchema();
    
    // 要件ファイルの読み込み
    const requirementFilePath = join(args.reqDir, `${requirementId}.require.json`);
    let requirement;
    
    try {
      const content = await Deno.readTextFile(requirementFilePath);
      requirement = JSON.parse(content);
    } catch (error) {
      console.error(`要件ファイル ${requirementFilePath} の読み込みに失敗しました: ${error.message}`);
      Deno.exit(1);
    }
    
    // 指定された要件が関数型でない場合はエラー
    if (requirement.implementationType !== "function") {
      console.error(`エラー: 要件 ${requirementId} は関数型ではありません (${requirement.implementationType})`);
      Deno.exit(1);
    }
    
    // 関数定義JSONへ変換
    const functionJson = convertRequirementToFunction(requirement, functionMetaSchema);
    
    // 出力ファイルパスの生成
    const outputFilePath = join(args.outDir, `${requirementId}.Function.config.json`);
    
    // 既存ファイルの存在チェック
    try {
      await Deno.stat(outputFilePath);
      if (!args.force) {
        console.error(`エラー: 出力ファイル ${outputFilePath} は既に存在します。上書きするには --force オプションを使用してください`);
        Deno.exit(1);
      }
    } catch (error) {
      // ファイルが存在しない場合は問題なし
      if (!(error instanceof Deno.errors.NotFound)) {
        throw error;
      }
    }
    
    // 結果の出力
    const jsonString = JSON.stringify(functionJson, null, 2);
    
    if (args.dryRun) {
      console.log("生成される関数定義JSON:");
      console.log(jsonString);
    } else {
      await Deno.writeTextFile(outputFilePath, jsonString);
      console.log(`関数定義JSONを ${outputFilePath} に出力しました`);
    }
  } catch (error) {
    console.error(`処理中にエラーが発生しました: ${error.message}`);
    Deno.exit(1);
  }
}

/**
 * 関数メタスキーマを読み込む
 * 
 * @returns 関数メタスキーマオブジェクト
 */
async function loadFunctionMetaSchema(): Promise<any> {
  try {
    const content = await Deno.readTextFile(FUNCTION_META_SCHEMA_PATH);
    return JSON.parse(content);
  } catch (error) {
    console.error(`関数メタスキーマ ${FUNCTION_META_SCHEMA_PATH} の読み込みに失敗しました: ${error.message}`);
    Deno.exit(1);
  }
}

/**
 * 要件定義から関数定義JSONを生成
 * 
 * @param requirement 要件定義オブジェクト
 * @param metaSchema 関数メタスキーマオブジェクト
 * @returns 関数定義JSONオブジェクト
 */
function convertRequirementToFunction(requirement: any, metaSchema: any): any {
  // 基本構造の作成
  const functionJson: any = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$metaSchema": "Function",
    "title": requirement.title,
    "description": requirement.description,
    "type": "function"
  };
  
  // outputInfoから関数情報をコピー
  if (requirement.outputInfo && requirement.outputInfo.function) {
    const functionInfo = requirement.outputInfo.function;
    
    // パラメータ情報
    if (functionInfo.parameters) {
      functionJson.parameters = functionInfo.parameters;
    }
    
    // 戻り値情報
    if (functionInfo.returnType) {
      functionJson.returnType = functionInfo.returnType;
    }
    
    // 非同期フラグ
    if (functionInfo.async !== undefined) {
      functionJson.async = functionInfo.async;
    }
  }
  
  // タグ情報
  if (requirement.tags && Array.isArray(requirement.tags)) {
    functionJson.tags = requirement.tags;
  }
  
  // その他のメタデータを追加
  functionJson.sideEffects = true;  // デフォルトでは副作用ありとする
  functionJson.deprecated = false;  // デフォルトでは非推奨でない
  
  // 例がある場合は例も含める
  if (requirement.examples && Array.isArray(requirement.examples)) {
    functionJson.examples = requirement.examples;
  }
  
  return functionJson;
}

// メイン関数を実行
if (import.meta.main) {
  main().catch(err => {
    console.error(`エラーが発生しました: ${err.message}`);
    Deno.exit(1);
  });
}
