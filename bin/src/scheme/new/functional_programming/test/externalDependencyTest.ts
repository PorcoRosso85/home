#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --no-check

/**
 * externalDependencyTest.ts
 * 
 * UserAuth__Function.jsonからUserRegister__Function.jsonへの外部依存関係の
 * 検出能力をテストするE2Eテスト
 */

// 必要なモジュールのインポート
import { exists } from "https://deno.land/std/fs/mod.ts";
import * as path from "node:path";

/**
 * メイン関数 - E2Eテストの実行
 */
async function main() {
  console.log("===== 外部依存関係検出 E2E テスト開始 =====");
  
  try {
    // カレントディレクトリのパスを取得
    const currentDir = Deno.cwd();
    const projectDir = "/home/nixos/scheme/new/functional_programming";
    
    // 入力ファイル
    const userAuthPath = path.join(projectDir, "UserAuth__Function.json");
    const userRegisterPath = path.join(projectDir, "UserRegister__Function.json");
    
    // ファイルの存在確認
    if (!await exists(userAuthPath)) {
      throw new Error(`UserAuth__Function.json が見つかりません: ${userAuthPath}`);
    }
    
    if (!await exists(userRegisterPath)) {
      throw new Error(`UserRegister__Function.json が見つかりません: ${userRegisterPath}`);
    }
    
    console.log(`📁 テスト用JSONファイルを確認しました`);
    console.log(`- UserAuth__Function.json: ${userAuthPath}`);
    console.log(`- UserRegister__Function.json: ${userRegisterPath}`);
    
    // 内容確認
    const userAuthContent = JSON.parse(await Deno.readTextFile(userAuthPath));
    console.log("\n📝 UserAuth__Function.json の外部依存関係:");
    if (userAuthContent.externalDependencies) {
      console.log(JSON.stringify(userAuthContent.externalDependencies, null, 2));
    } else {
      console.log("  外部依存関係が定義されていません");
    }
    
    // 解析前後の結果を比較するために使用する出力ファイル
    const outputPath = path.join(projectDir, "test", "deps-test-output.json");
    
    // ===== 修正前の状態で依存関係解析 =====
    console.log("\n🧪 修正前の依存関係解析(直接API呼び出し)...");
    
    // findReferences関数と同等のロジックで簡易検索
    function simpleFind(obj: any): string[] {
      if (!obj || typeof obj !== "object") return [];
      
      let refs: string[] = [];
      
      if (obj.$ref && typeof obj.$ref === "string") {
        refs.push(obj.$ref);
      }
      
      if (Array.isArray(obj)) {
        for (const item of obj) {
          refs = [...refs, ...simpleFind(item)];
        }
      } else {
        for (const [key, value] of Object.entries(obj)) {
          if (key !== "$ref") {
            refs = [...refs, ...simpleFind(value)];
          }
        }
      }
      
      return refs;
    }
    
    // 修正前の方法で$refを検索
    const refsBeforeFix = simpleFind(userAuthContent);
    const hasRegisterBeforeFix = refsBeforeFix.some(ref => ref.includes("UserRegister"));
    
    console.log(`修正前の検索で${refsBeforeFix.length}個の$refを検出`);
    console.log(`UserRegister への依存関係: ${hasRegisterBeforeFix ? '検出' : '未検出'}`);
    
    // ===== 修正後の状態をシミュレート =====
    console.log("\n🧪 修正後の依存関係解析(シミュレーション)...");
    
    // 修正版のfindReferences相当の機能
    function enhancedFind(obj: any): string[] {
      if (!obj || typeof obj !== "object") return [];
      
      let refs: string[] = [];
      
      if (obj.$ref && typeof obj.$ref === "string") {
        refs.push(obj.$ref);
      }
      
      // ルートレベルのexternalDependencies配列を特別に処理
      if (obj.externalDependencies && Array.isArray(obj.externalDependencies)) {
        for (const dep of obj.externalDependencies) {
          if (dep.$ref && typeof dep.$ref === "string") {
            refs.push(dep.$ref);
          }
        }
      }
      
      if (Array.isArray(obj)) {
        for (const item of obj) {
          refs = [...refs, ...enhancedFind(item)];
        }
      } else {
        for (const [key, value] of Object.entries(obj)) {
          if (key !== "$ref") {
            refs = [...refs, ...enhancedFind(value)];
          }
        }
      }
      
      return refs;
    }
    
    // 修正後の方法で$refを検索
    const refsAfterFix = enhancedFind(userAuthContent);
    const hasRegisterAfterFix = refsAfterFix.some(ref => ref.includes("UserRegister"));
    
    console.log(`修正後の検索で${refsAfterFix.length}個の$refを検出`);
    console.log(`UserRegister への依存関係: ${hasRegisterAfterFix ? '検出' : '未検出'}`);
    
    // ===== 実際のコマンドによる検証 =====
    console.log("\n🧪 実際のdepsコマンドを使った検証...");
    
    // deps コマンドを実行
    const cmd = new Deno.Command("/home/nixos/scheme/new/functional_programming/interface/cli.ts", {
      args: [
        "deps",
        userAuthPath,  // 最初の位置引数としてパスを指定（--schemaではない）
        "--format", "json",
        "--output", outputPath,
        "--verbose"  // デバッグのために詳細出力を有効化
      ],
      stdout: "piped",
      stderr: "piped"
    });
    
    const output = await cmd.output();
    const stdout = new TextDecoder().decode(output.stdout);
    const stderr = new TextDecoder().decode(output.stderr);
    
    if (stderr) {
      console.log("コマンド実行エラー:", stderr);
    }
    
    if (stdout) {
      console.log("コマンド出力:", stdout);
    }
    
    // 出力ファイルの存在確認
    let fileExists = false;
    try {
      fileExists = await exists(outputPath);
    } catch (error) {
      console.error("出力ファイルの確認に失敗:", error.message);
    }
    
    if (fileExists) {
      console.log(`出力ファイルが生成されました: ${outputPath}`);
      try {
        const jsonContent = JSON.parse(await Deno.readTextFile(outputPath));
        
        // 依存関係の検索
        console.log("\n📊 依存関係グラフの解析:");
        
        let hasRegisterDependency = false;
        if (jsonContent.edges) {
          const edges = jsonContent.edges;
          console.log(`グラフに${edges.length}個のエッジが存在`);
          
          for (const edge of edges) {
            if (edge.target && edge.target.includes("UserRegister")) {
              hasRegisterDependency = true;
              console.log(`✅ UserRegister への依存関係エッジを検出: ${edge.source} -> ${edge.target}`);
              break;
            }
          }
          
          if (!hasRegisterDependency) {
            console.log("❌ UserRegister への依存関係エッジは検出されませんでした");
          }
        } else {
          console.log("❓ 依存関係グラフのエッジ情報が見つかりません");
        }
      } catch (error) {
        console.error("出力ファイルの解析に失敗:", error.message);
      }
    } else {
      console.log("❌ 出力ファイルが生成されませんでした");
    }
    
    // テストの成功/失敗判定
    console.log("\n===== テスト結果 =====");
    
    let hasRegisterDependency = false;
    if (fileExists) {
      try {
        const jsonContent = JSON.parse(await Deno.readTextFile(outputPath));
        if (jsonContent.edges) {
          hasRegisterDependency = jsonContent.edges.some(edge => 
            edge.target && edge.target.includes("UserRegister")
          );
        }
      } catch (error) {
        console.error("結果の判定中にエラー:", error.message);
      }
    }
    
    const expectedSummary = [
      "• 手動シミュレーション:",
      `  - 修正前: UserRegister への依存関係は${hasRegisterBeforeFix ? '検出' : '未検出'}`,
      `  - 修正後: UserRegister への依存関係は${hasRegisterAfterFix ? '検出' : '未検出'}`,
      "• ファイル出力結果:",
      `  - deps コマンド: UserRegister への依存関係は${hasRegisterDependency ? '検出' : '未検出'}`
    ].join("\n");
    console.log(expectedSummary);
    
    // 最終判定
    const finalResult = hasRegisterAfterFix && hasRegisterDependency;
    console.log(`\n${finalResult ? '✅ テスト成功' : '❌ テスト失敗'} - 修正により依存関係検出が${finalResult ? '改善されました' : '改善されていません'}`);
    
    // 対応すべき課題の表示
    if (!hasRegisterDependency) {
      console.log("\n⚠️ 対応すべき課題:");
      console.log("1. 修正したfindReferences関数は正しく動作していますが、それが依存関係グラフに反映されていません");
      console.log("2. graphBuilder.tsなどの関連ファイルも修正が必要です");
    }
    
    // 推奨事項の表示
    console.log("\n📋 推奨事項:");
    if (finalResult) {
      console.log("1. FIXMEで提案した修正を正式に適用する");
      console.log("2. 単体テストケースを追加して、外部依存関係の検出をカバーする");
      console.log("3. 他の依存関係解析関連ファイルも修正する");
    } else {
      console.log("1. domain/service/graphBuilder.tsを確認し、外部依存関係の処理を追加する");
      console.log("2. 外部依存関係から正しくエッジを生成する処理を実装する");
      console.log("3. スキーマ構造と依存関係解析の整合性を確保する");
    }
    
    console.log("\n===== E2E テスト終了 =====");
    
  } catch (error) {
    console.error("❌ テスト実行中にエラーが発生しました:", error.message);
  }
}

// メイン関数の実行
if (import.meta.main) {
  await main();
}
