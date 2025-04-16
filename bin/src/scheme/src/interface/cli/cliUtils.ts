/**
 * CLI用のユーティリティ関数
 */
import { join } from "https://deno.land/std@0.220.1/path/mod.ts";

/**
 * CLIコマンドのヘルプを表示
 */
export function showHelp() {
  console.log(`
メタスキーマ管理CLI - 使用方法:

  register <metaSchemaPath> - メタスキーマを登録
  generate <metaSchemaId> <configPath> <outputPath> - スキーマを生成
  validate <schemaPath> - スキーマを検証
  diagnose meta <metaSchemaPath> - メタスキーマを診断
  diagnose config <configPath> <metaSchemaId> [<metaSchemaPath>] - 設定ファイルを診断
  list - 登録済みのメタスキーマ一覧を表示
  deps <型名.メタスキーマ> - 型の依存関係を再帰的に表示
  convert-refs [ファイルパス] - スキーマファイル内の$ref参照を新形式に変換
  req-deps <サブコマンド> - 要件間の依存関係を解析
  req-to-function <要件ID> - 要件から関数定義JSONを生成
  output-paths - 要件から出力パスと依存関係を表示
  req-gen <コマンド> [オプション] - 統一要件JSONの生成と管理
  generate-types - 統一要件から型スキーマを一括生成

オプション:
  --help, -h        このヘルプを表示
  --verbose, -v     詳細な出力を表示
  --show-deps, -d   依存関係を表示 (一部のコマンドのみ)

例:
  # メタスキーマ操作
  ./cli.ts register ./data/meta/String.meta.json
  ./cli.ts generate StringTypeMetaSchema ./data/config/UserId.String.config.json ./data/generated/UserId.String.schema.json
  # (注: ./data/config ディレクトリは今後使用されません)
  ./cli.ts validate ./data/generated/UserId.String.schema.json
  ./cli.ts diagnose meta ./data/meta/String.meta.json
  ./cli.ts diagnose config ./data/config/UserId.String.config.json StringTypeMetaSchema
  ./cli.ts list
  
  # 依存関係表示
  ./cli.ts deps User.Struct
  ./cli.ts req-deps deps UserAuthentication
  ./cli.ts output-paths --show-deps
  ./cli.ts output-paths --format=mermaid
  ./cli.ts function-deps
  ./cli.ts function-deps UserAuthentication --format=tree
  
  # 参照変換
  ./cli.ts convert-refs --dir=./data/generated
  ./cli.ts convert-refs ./data/generated/User.Struct.schema.json
  
  # 要件・型変換
  ./cli.ts req-to-function UserAuthentication
  ./cli.ts generate-types
  
  # 統一要件管理
  ./cli.ts req-gen create NewFeature --title="新機能" --desc="新機能の説明" --type=function
  ./cli.ts req-gen list
  ./cli.ts req-gen validate UserAuthentication
  ./cli.ts req-gen convert ExistingFeature
  `);
}

/**
 * 必要なディレクトリが存在するか確認し、存在しない場合は作成する
 */
export async function ensureDirectoriesExist(dirs: string[]): Promise<void> {
  for (const dir of dirs) {
    try {
      await Deno.stat(dir);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        console.log(`ディレクトリ ${dir} が存在しないため作成します`);
        await Deno.mkdir(dir, { recursive: true });
      } else {
        throw error;
      }
    }
  }
}

/**
 * 統一要件メタスキーマを読み込む
 * 
 * @param metaDir メタスキーマディレクトリ
 * @returns 統一要件メタスキーマオブジェクト
 */
export async function loadRequirementMetaSchema(metaDir: string): Promise<any> {
  const metaSchemaPath = join(metaDir, "Requirement.meta.json");
  
  try {
    const content = await Deno.readTextFile(metaSchemaPath);
    return JSON.parse(content);
  } catch (error) {
    console.error(`統一要件メタスキーマ ${metaSchemaPath} の読み込みに失敗しました: ${error.message}`);
    Deno.exit(1);
  }
}
