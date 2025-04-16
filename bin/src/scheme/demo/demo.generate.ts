#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run

/**
 * User型とその依存型を生成するデモスクリプト
 */
async function main() {
  // 必要なディレクトリの存在確認と作成
  await ensureDirectoryExists("./data/generated");

  // スキーマ生成の確認
  console.log("\n=== UserId型の生成 ===");
  await runCommand("generate String ./data/config/UserId.String.config.json ./data/generated/UserId.String.schema.json");

  console.log("\n=== Email型の生成 ===");
  await runCommand("generate String ./data/config/Email.String.config.json ./data/generated/Email.String.schema.json");

  console.log("\n=== Name型の生成 ===");
  await runCommand("generate String ./data/config/Name.String.config.json ./data/generated/Name.String.schema.json");
  
  console.log("\n=== Address型の生成 ===");
  await runCommand("generate String ./data/config/Address.String.config.json ./data/generated/Address.String.schema.json");
  
  // 機能型の生成
  console.log("\n=== RegistrationError型の生成 ===");
  await runCommand("generate Struct ./data/config/RegistrationError.Struct.config.json ./data/generated/RegistrationError.Struct.schema.json");
  
  // 構造体型の生成
  console.log("\n=== User型の生成 ===");
  await runCommand("generate Struct ./data/config/User.Struct.config.json ./data/generated/User.Struct.schema.json");
  
  // 関数型の生成
  console.log("\n=== UserRegister関数型の生成 ===");
  await runCommand("generate Function ./data/config/UserRegister.Function.config.json ./data/generated/UserRegister.Function.schema.json");
  
  // 生成されたスキーマの確認
  console.log("\n=== 生成されたUser型スキーマの内容 ===");
  const userSchema = await Deno.readTextFile("./data/generated/User.Struct.schema.json");
  console.log(userSchema);
  
  // 生成されたRegistrationError型スキーマの確認
  console.log("\n=== 生成されたRegistrationError型スキーマの内容 ===");
  const registrationErrorSchema = await Deno.readTextFile("./data/generated/RegistrationError.Struct.schema.json");
  console.log(registrationErrorSchema);
  
  // 生成された関数型スキーマの確認
  console.log("\n=== 生成されたUserRegister関数型スキーマの内容 ===");
  const userRegisterSchema = await Deno.readTextFile("./data/generated/UserRegister.Function.schema.json");
  console.log(userRegisterSchema);
  
  console.log("\n=== デモ完了 ===");
}

/**
 * ディレクトリの存在を確認し、存在しない場合は作成する
 * 
 * @param dir 作成するディレクトリパス
 */
async function ensureDirectoryExists(dir: string): Promise<void> {
  try {
    const dirInfo = await Deno.stat(dir);
    if (!dirInfo.isDirectory) {
      throw new Error(`${dir}はディレクトリではありません`);
    }
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      console.log(`ディレクトリ ${dir} が見つからないため作成します`);
      await Deno.mkdir(dir, { recursive: true });
    } else {
      throw error;
    }
  }
}

/**
 * CLIコマンドを実行する
 * 
 * @param commandStr コマンド文字列
 */
async function runCommand(commandStr: string): Promise<void> {
  const command = `deno run --allow-read --allow-write ./src/interface/cliController.ts ${commandStr}`;
  console.log(`$ ${command}`);
  
  const p = Deno.run({
    cmd: command.split(" "),
    stdout: "piped",
    stderr: "piped",
  });
  
  const [status, stdout, stderr] = await Promise.all([
    p.status(),
    p.output(),
    p.stderrOutput(),
  ]);
  p.close();
  
  const decoderOut = new TextDecoder();
  const decoderErr = new TextDecoder();
  
  const outStr = decoderOut.decode(stdout);
  const errStr = decoderErr.decode(stderr);
  
  if (outStr) console.log(outStr);
  if (errStr) console.error(errStr);
  
  if (!status.success) {
    throw new Error(`コマンド実行に失敗しました: ${commandStr}`);
  }
}

// メイン関数を実行
if (import.meta.main) {
  main().catch(err => {
    console.error("エラーが発生しました:", err.message);
    Deno.exit(1);
  });
}
