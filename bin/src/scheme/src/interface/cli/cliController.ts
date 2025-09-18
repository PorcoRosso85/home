/**
 * CLI制御用コントローラークラス
 */
import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { showHelp, ensureDirectoriesExist } from "../cli/cliUtils.ts";
import { executeRequirementsGeneratorCommand } from "../cli/requirementsCommands.ts";
import { executeGenerateTypesCommand } from "../cli/typeGenerationCommands.ts";
import { DIRECTORIES } from "../../infrastructure/variables.ts";

// コマンドクラスのインポート
import { Command } from "../../application/command.ts";
import { RegisterCommand } from "../../application/registerCommand.ts";
import { GenerateCommand } from "../../application/generateCommand.ts";
import { ValidateCommand } from "../../application/validateCommand.ts";
import { DiagnoseCommand } from "../../application/diagnoseCommand.ts";
import { ListCommand } from "../../application/listCommand.ts";
import { DepsCommand } from "../../application/depsCommand.ts";
import { RequirementsDepsCommand } from "../../application/requirementsDepsCommand.ts";
import { RequirementsToFunctionCommand } from "../../application/requirementsToFunctionCommand.ts";
import { ConvertRefsCommand } from "../../application/convertRefsCommand.ts";
import { OutputPathsCommand } from "../../application/outputPathsCommand.ts";
import { OutputTypePathCommand } from "../../application/outputTypePathCommand.ts";
import { FunctionDependencyCommand } from "../../application/functionDependencyCommand.ts";

// インフラストラクチャとサービスのインポート
import { ValidationServiceImpl } from "../../domain/validationService.ts";
import { GenerationServiceImpl } from "../../domain/generationService.ts";
import { MetaSchemaRegistryService } from "../../application/metaSchemaRegistryService.ts";
import { FileMetaSchemaRepository } from "../../infrastructure/fileMetaSchemaRepository.ts";
import { FileSystemReader } from "../../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../../infrastructure/fileSystemWriter.ts";

/**
 * 統合CLIコントローラークラス
 * すべてのコマンドを統合的に管理し、適切な処理にディスパッチする
 */
export class IntegratedCliController {
  private commands: Map<string, Command>;
  private fileReader: FileSystemReader;
  private fileWriter: FileSystemWriter;
  private defaultRequirementsDir: string = DIRECTORIES.REQUIREMENTS;
  private defaultGeneratedDir: string = DIRECTORIES.GENERATED;
  private defaultMetaDir: string = DIRECTORIES.META;
  private defaultOldReqDir: string = DIRECTORIES.OLD_REQUIREMENTS;
  private defaultOldConfigDir: string = DIRECTORIES.OLD_CONFIG;
  
  /**
   * コンストラクタ
   */
  constructor() {
    this.commands = new Map<string, Command>();
    
    // 依存関係の構築
    this.fileReader = new FileSystemReader();
    this.fileWriter = new FileSystemWriter();
    const metaSchemaRepository = new FileMetaSchemaRepository(this.fileReader, this.defaultMetaDir);
    const validationService = new ValidationServiceImpl();
    const generationService = new GenerationServiceImpl();
    
    const registryService = new MetaSchemaRegistryService(
      metaSchemaRepository,
      validationService,
      generationService
    );
    
    // コマンドの登録
    this.commands.set("register", new RegisterCommand(registryService, this.fileReader));
    this.commands.set("generate", new GenerateCommand(registryService, this.fileReader, this.fileWriter));
    this.commands.set("validate", new ValidateCommand(registryService, this.fileReader));
    this.commands.set("diagnose", new DiagnoseCommand(registryService, this.fileReader));
    this.commands.set("list", new ListCommand(registryService));
    this.commands.set("deps", new DepsCommand(this.fileReader, this.defaultGeneratedDir));
    this.commands.set("convert-refs", new ConvertRefsCommand(this.fileReader, this.fileWriter, this.defaultGeneratedDir));
    
    // アプリケーション層のユースケースを呼び出すコマンドを登録
    this.commands.set("req-deps", new RequirementsDepsCommand(this.fileReader, this.defaultRequirementsDir));
    this.commands.set("req-to-function", new RequirementsToFunctionCommand(
      this.fileReader, 
      this.fileWriter, 
      this.defaultRequirementsDir, 
      this.defaultGeneratedDir, 
      this.defaultMetaDir
    ));
    this.commands.set("output-paths", new OutputPathsCommand(this.fileReader, this.defaultRequirementsDir, this.defaultGeneratedDir));
    this.commands.set("output-type-path", new OutputTypePathCommand(this.fileReader, this.defaultRequirementsDir, this.defaultGeneratedDir));
    this.commands.set("function-deps", new FunctionDependencyCommand(this.fileReader, this.defaultRequirementsDir, this.defaultGeneratedDir));
  }
  
  /**
   * メイン処理
   */
  async main(): Promise<void> {
    try {
      // コマンドライン引数の解析
      const args = parse(Deno.args, {
        boolean: ['help', 'verbose', 'force', 'show-deps', 'show-func-deps'],
        string: ['outDir', 'oldReqDir', 'oldConfigDir', 'metaDir', 'title', 'desc', 'type', 'path', 'deps', 'generatedDir'],
        alias: { h: 'help', v: 'verbose', d: 'show-deps' },
        default: {
          outDir: this.defaultRequirementsDir,
          oldReqDir: this.defaultOldReqDir,
          oldConfigDir: this.defaultOldConfigDir,
          metaDir: this.defaultMetaDir,
          generatedDir: this.defaultGeneratedDir,
          force: false
        }
      });
      
      // コマンド名の取得
      const commandName = args._[0] as string;
      
      // ヘルプ表示の場合
      if (!commandName || args.help) {
        showHelp();
        return;
      }
      
      // メタスキーマリポジトリの初期化
      if (commandName === "list" || commandName === "register" || 
          commandName === "generate" || commandName === "validate" || 
          commandName === "diagnose") {
        await this.initializeRepository();
      }
      
      // ディレクトリの確認と作成
      if (commandName === "req-gen" || commandName === "generate-types") {
        await ensureDirectoriesExist([
          args.outDir,
          args.metaDir,
          args.generatedDir
        ]);
      }
      
      // 役割分担：標準コマンド
      if (this.commands.has(commandName)) {
        // 通常のコマンドの実行
        const command = this.commands.get(commandName)!;
        await command.execute(args);
        return;
      }

      // 役割分担：統一要件生成コマンド
      if (commandName === "req-gen") {
        await executeRequirementsGeneratorCommand(args);
        return;
      }

      // 役割分担：型生成コマンド
      if (commandName === "generate-types") {
        await executeGenerateTypesCommand(args);
        return;
      }

      // 未知のコマンド
      throw new Error(`未知のコマンド: ${commandName}`);
      
    } catch (error) {
      console.error(`エラー: ${error.message}`);
      Deno.exit(1);
    }
  }
  
  /**
   * メタスキーマリポジトリの初期化
   */
  private async initializeRepository(): Promise<void> {
    try {
      // メタスキーマリポジトリを取得
      const metaSchemaRepository = (this.commands.get("list") as ListCommand)["registryService"]["metaSchemaRepository"] as FileMetaSchemaRepository;
      
      // リポジトリの初期化
      await metaSchemaRepository.initialize();
    } catch (error) {
      console.warn(`メタスキーマリポジトリの初期化に失敗しました: ${error.message}`);
    }
  }
}
