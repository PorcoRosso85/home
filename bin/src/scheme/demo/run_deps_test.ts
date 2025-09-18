#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-run --allow-read

/**
 * 型依存関係解析のテスト用スクリプト
 * 
 * このスクリプトは、型依存関係解析コマンドを実行し、結果を表示します。
 */

// Denoのプロセス実行APIを使用してコマンドを実行する関数
async function runCommand(command: string, args: string[]): Promise<void> {
  console.log(`実行: ${command} ${args.join(" ")}`);
  
  try {
    const process = Deno.run({
      cmd: [command, ...args],
      stdout: "inherit",
      stderr: "inherit"
    });
    
    console.log("プロセス開始");
    const status = await process.status();
    process.close();
    
    console.log(`プロセス終了 (コード: ${status.code})`);
    if (!status.success) {
      console.error(`コマンド実行エラー (終了コード: ${status.code})`);
    }
  } catch (error) {
    console.error(`コマンド実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

// ファイルの存在確認関数
async function fileExists(path: string): Promise<boolean> {
  try {
    await Deno.stat(path);
    return true;
  } catch (e) {
    return false;
  }
}

// メイン関数
async function main() {
  console.log("型依存関係解析のテスト開始...\n");
  
  // cliController.tsのフルパス
  const cliPath = "/home/nixos/scheme/src/interface/cliController.ts";
  
  try {
    // 生成済みのスキーマを確認
    console.log("生成済みのスキーマファイルを確認します...");
    
    // ディレクトリの存在確認
    const genDir = "/home/nixos/scheme/data/generated";
    const userSchemaPath = `${genDir}/User.Struct.schema.json`;
    const emailSchemaPath = `${genDir}/Email.String.schema.json`;
    
    // ディレクトリとファイルの存在確認
    const dirExists = await fileExists(genDir);
    const userExists = await fileExists(userSchemaPath);
    const emailExists = await fileExists(emailSchemaPath);
    
    console.log(`生成ディレクトリの存在: ${dirExists ? "あり" : "なし"}`);
    console.log(`User.Struct スキーマの存在: ${userExists ? "あり" : "なし"}`);
    console.log(`Email.String スキーマの存在: ${emailExists ? "あり" : "なし"}`);
    
    // data/generatedディレクトリ内のファイルを一覧表示
    console.log("\nディレクトリ内のファイル:");
    if (dirExists) {
      await runCommand("ls", ["-la", genDir]);
    } else {
      console.log("生成ディレクトリが存在しません");
    }
    
    console.log("\n");
    
    // User.Struct型の依存関係を解析（ファイルが存在する場合のみ）
    if (userExists) {
      console.log("User.Struct 型の依存関係を再帰的に解析します:");
      await runCommand("deno", ["run", "--allow-read", "--allow-write", "--allow-run", cliPath, "deps", "User.Struct", "--debug"]);
    } else {
      console.log("User.Struct スキーマが存在しないためスキップします");
    }
    
    console.log("\n");
    
    // UserRegister.Function型の依存関係を解析
    const userRegisterPath = `${genDir}/UserRegister.Function.schema.json`;
    const userRegisterExists = await fileExists(userRegisterPath);
    console.log(`UserRegister.Function スキーマの存在: ${userRegisterExists ? "あり" : "なし"}`);
    
    if (userRegisterExists) {
      console.log("\nUserRegister.Function 型の依存関係を再帰的に解析します:");
      await runCommand("deno", ["run", "--allow-read", "--allow-write", "--allow-run", cliPath, "deps", "UserRegister.Function", "--debug"]);
    } else {
      console.log("UserRegister.Function スキーマが存在しないためスキップします");
    }
    
    console.log("\nテスト完了");
  } catch (error) {
    console.error(`エラーが発生しました: ${error.message}`);
    Deno.exit(1);
  }
}

// スクリプトが直接実行された場合のみメイン関数を実行
if (import.meta.main) {
  await main();
}
