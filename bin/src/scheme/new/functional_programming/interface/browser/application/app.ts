/**
 * app.ts
 * 
 * アプリケーションのメインロジック
 */

import { CommandInfo } from '../../client/types.ts';
import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';
import { Graph } from '/home/nixos/scheme/new/functional_programming/domain/entities/graph.ts';
import { TreeNode } from '../domain/models/treeNode.ts';
import { SchemaService } from '../domain/service/schemaService.ts';
import { renderTree } from './components/treeView.ts';
import { renderDetailView } from './components/detailView.ts';
import {
  createHeader,
  createMainContent,
  createCommandPanel,
  createFooter,
  showLoading,
  hideLoading,
  showError
} from './components/uiComponents.ts';
import {
  updateCommandList,
  showCommandHelp,
  showCommandResult
} from './components/commandPanel.ts';
import { CommonClient } from '../../client/types.ts';

/**
 * アプリケーション状態
 */
interface AppState {
  client: CommonClient;
  commands: CommandInfo[];
  selectedCommand?: CommandInfo;
  functionData: FunctionSchema[];
  graphData?: Graph;
  selectedNode?: TreeNode;
}

/**
 * アプリケーションクラス
 */
export class App {
  private state: AppState;
  private rootElement: HTMLElement;
  private schemaService: SchemaService;

  /**
   * コンストラクタ
   * @param client APIクライアント
   * @param rootElement ルート要素
   * @param schemaService スキーマサービス
   */
  constructor(
    client: CommonClient, 
    rootElement: HTMLElement,
    schemaService: SchemaService
  ) {
    this.state = {
      client,
      commands: [],
      functionData: []
    };
    this.rootElement = rootElement;
    this.schemaService = schemaService;
  }

  /**
   * アプリケーションの初期化
   */
  async initialize(): Promise<void> {
    try {
      // UIの初期設定
      this.setupUI();
      
      // データの初期ロード
      showLoading();
      await this.loadInitialData();
      hideLoading();
    } catch (error) {
      console.error('アプリケーション初期化エラー:', error);
      showError(`初期化エラー: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * UIの初期設定
   */
  private setupUI(): void {
    if (!this.rootElement) {
      throw new Error('アプリケーションコンテナが見つかりません。id="app"の要素が必要です。');
    }
    
    // ヘッダー
    const header = createHeader(() => this.refreshData());
    
    // メインコンテンツ
    const content = createMainContent();
    
    // コマンドパネル
    const commandPanel = createCommandPanel();
    
    // フッター
    const footer = createFooter();
    
    // DOM構築
    this.rootElement.appendChild(header);
    this.rootElement.appendChild(content);
    this.rootElement.appendChild(commandPanel);
    this.rootElement.appendChild(footer);
  }

  /**
   * データの更新
   */
  private async refreshData(): Promise<void> {
    showLoading();
    await this.loadInitialData();
    hideLoading();
  }

  /**
   * 初期データのロード
   */
  private async loadInitialData(): Promise<void> {
    try {
      // コマンドのロード
      this.state.commands = await this.state.client.getAvailableCommands();
      this.updateCommandList();
      
      // スキーマリストのロード
      const schemaList = await this.schemaService.getSchemaList();
      
      // すべてのスキーマをロード
      this.state.functionData = await this.schemaService.getAllSchemas();
      
      // ルートスキーマが存在する場合は依存関係グラフをロード
      if (schemaList.length > 0) {
        this.state.graphData = await this.schemaService.getDependencyGraph(schemaList[0]);
      }
      
      // ビューの更新
      this.updateTreeView();
    } catch (error) {
      console.error('データロードエラー:', error);
      showError(`データロードエラー: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * コマンドリストの更新
   */
  private updateCommandList(): void {
    const commandList = document.getElementById('command-list');
    if (!commandList) return;
    
    updateCommandList(
      commandList, 
      this.state.commands, 
      (name) => this.selectCommand(name)
    );
  }

  /**
   * コマンドの選択
   */
  private selectCommand(commandName: string): void {
    this.state.selectedCommand = this.state.commands.find(cmd => cmd.name === commandName);
    if (this.state.selectedCommand) {
      const commandPanel = document.getElementById('command-panel');
      if (commandPanel) {
        showCommandHelp(
          commandPanel, 
          this.state.selectedCommand, 
          (cmd, args) => this.executeCommand(cmd, args)
        );
      }
    }
  }

  /**
   * コマンドの実行
   */
  private async executeCommand(commandName: string, args: string[]): Promise<void> {
    const resultDiv = document.getElementById('command-result');
    if (!resultDiv) return;
    
    resultDiv.innerHTML = '<div class="loading">実行中...</div>';
    
    try {
      const result = await this.state.client.executeCommand(commandName, args);
      showCommandResult(resultDiv, result);
    } catch (error) {
      showCommandResult(resultDiv, error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * ツリービューの更新
   */
  private async updateTreeView(): Promise<void> {
    const treeView = document.getElementById('directory-tree');
    if (!treeView) return;
    
    // ツリービューの構築
    const treeData = await this.schemaService.buildSchemaTree();
    renderTree(treeView, treeData, (node) => this.selectTreeNode(node));
  }

  /**
   * ツリーノードの選択
   */
  private selectTreeNode(node: TreeNode): void {
    this.state.selectedNode = node;
    
    // 依存関係ビューの更新
    // 詳細ビューは表示しない
    /*
    const dependencyView = document.getElementById('dependency-view');
    if (dependencyView) {
      renderDetailView(dependencyView, node, this.state.graphData);
    }
    */
  }
}
