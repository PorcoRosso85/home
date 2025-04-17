#!/usr/bin/env -S deno run --allow-read --allow-write

import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { DisplayHelper } from "./displayHelper.ts";
import { Command } from "../application/command.ts";
import { RegisterCommand } from "../application/registerCommand.ts";
import { GenerateCommand } from "../application/generateCommand.ts";
import { ValidateCommand } from "../application/validateCommand.ts";
import { DiagnoseCommand } from "../application/diagnoseCommand.ts";
import { ListCommand } from "../application/listCommand.ts";
import { DepsCommand } from "../application/depsCommand.ts";
import { RequirementsDepsCommand } from "../application/requirementsDepsCommand.ts";
import { RequirementsToFunctionCommand } from "../application/requirementsToFunctionCommand.ts";
import { ValidationServiceImpl } from "../domain/validationService.ts";
import { GenerationServiceImpl } from "../domain/generationService.ts";
import { MetaSchemaRegistryService } from "../application/metaSchemaRegistryService.ts";
import { FileMetaSchemaRepository } from "../infrastructure/fileMetaSchemaRepository.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../infrastructure/fileSystemWriter.ts";

/**
 * CLIコントローラークラス
 * コマンドライン引数を解析し、適切なコマンドにディスパッチする
 */
class CliController {
  private displayHelper: DisplayHelper;
  private commands: Map<string, Command>;
  
  /**
   * コンストラクタ
   */
  constructor() {
    this.displayHelper = new DisplayHelper();
    this.commands = new Map<string, Command>();
    
    // 依存関係の構築
    const fileReader = new FileSystemReader();
    const fileWriter = new FileSystemWriter();
    const metaSchemaRepository = new FileMetaSchemaRepository(fileReader, "/home/nixos/scheme/data/meta");
    const validationService = new ValidationServiceImpl();
    const generationService = new GenerationServiceImpl();
    
    const registryService = new MetaSchemaRegistryService(
      metaSchemaRepository,
      validationService,
      generationService
    );
    
    // コマンドの登録
    this.commands.set("register", new RegisterCommand(registryService, fileReader));
    this.commands.set("generate", new GenerateCommand(registryService, fileReader, fileWriter));
    this.commands.set("validate", new ValidateCommand(registryService, fileReader));
    this.commands.set("diagnose", new DiagnoseCommand(registryService, fileReader));
    this.commands.set("list", new ListCommand(registryService));
    this.commands.set("deps", new DepsCommand(fileReader, "/home/nixos/scheme/data/generated"));
    
    // アプリケーション層のユースケースを呼び出すコマンドを登録
    this.commands.set("req-deps", new RequirementsDepsCommand(fileReader, "/home/nixos/scheme/data/requirements"));
    this.commands.set("req-to-function", new RequirementsToFunctionCommand(
      fileReader, 
      fileWriter, 
      "/home/nixos/scheme/data/requirements", 
      "/home/nixos/scheme/data/config", 
      "/home/nixos/scheme/data/meta"
    ));
  }
  
  /**
   * メイン処理
   */
  async main(): Promise<void> {
    try {
      // コマンドライン引数の解析
      const args = parse(Deno.args, {
        boolean: ['help', 'verbose'],
        alias: { h: 'help', v: 'verbose' },
      });
      
      // コマンド名の取得
      const commandName = args._[0] as string;
      
      // ヘルプ表示の場合
      if (!commandName || args.help) {
        this.displayHelper.showHelp();
        return;
      }
      
      // メタスキーマリポジトリの初期化
      await this.initializeRepository();
      
      // コマンドの取得と実行
      const command = this.commands.get(commandName);
      if (!command) {
        throw new Error(`未知のコマンド: ${commandName}`);
      }
      
      // コマンドの実行
      await command.execute(args);
      
    } catch (error) {
      this.displayHelper.displayError(error.message);
      Deno.exit(1);
    }
  }
  
  /**
   * メタスキーマリポジトリの初期化
   */
  private async initializeRepository(): Promise<void> {
    // メタスキーマリポジトリを取得
    const metaSchemaRepository = (this.commands.get("list") as ListCommand)["registryService"]["metaSchemaRepository"] as FileMetaSchemaRepository;
    
    // リポジトリの初期化
    await metaSchemaRepository.initialize();
  }
}

// スクリプトを実行
if (import.meta.main) {
  const controller = new CliController();
  await controller.main();
}
