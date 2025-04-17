import NodeRepository from '../repositories/NodeRepository';
import EdgeRepository from '../repositories/EdgeRepository';
import SubgraphRepository from '../repositories/SubgraphRepository';
import MetadataRepository from '../repositories/MetadataRepository';
import GraphDataService from './GraphDataService';
import { 
  FrontendNodeType, 
  HighlightDataType, 
  NodesMapType, 
  EdgeType, 
  SubgraphType, 
  MetadataType,
  StorageInfoType,
  FileNodeType,
  FunctionDependencyType,
  GraphValidationResultType,
  ExportFileType,
  NodeType
} from '../types';

/**
 * ノードデータに関連するサービスクラス
 */
class NodeService {
  private nodeRepository: NodeRepository;
  private edgeRepository: EdgeRepository;
  private subgraphRepository: SubgraphRepository;
  private metadataRepository: MetadataRepository;
  private graphDataService: GraphDataService;

  constructor() {
    this.nodeRepository = new NodeRepository();
    this.edgeRepository = new EdgeRepository();
    this.subgraphRepository = new SubgraphRepository();
    this.metadataRepository = new MetadataRepository();
    this.graphDataService = new GraphDataService();
  }

  /**
   * LocalStorageの使用状況を取得
   */
  getStorageInfo(): StorageInfoType {
    return this.graphDataService.getStorageInfo();
  }

  /**
   * すべてのデータをリセット（LocalStorageからクリア）
   */
  async resetAllData(): Promise<boolean> {
    return this.graphDataService.resetAllData();
  }

  // =========== ノード操作 ===========

  /**
   * ノードデータを取得する
   * @returns ノードデータのマップ
   */
  async getNodes(): Promise<NodesMapType> {
    return this.nodeRepository.getNodes();
  }

  /**
   * 指定されたIDのノードを取得
   * @param id ノードID
   * @returns ノードデータ
   */
  async getNode(id: string): Promise<NodeType | null> {
    return this.nodeRepository.getNode(id);
  }

  /**
   * 新しいノードを追加または既存のノードを更新
   * @param id ノードID
   * @param nodeData ノードデータ
   * @returns 成功したかどうか
   */
  async saveNode(id: string, nodeData: Partial<NodeType>): Promise<boolean> {
    const result = await this.nodeRepository.saveNode(id, nodeData);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  /**
   * 指定されたIDのノードを削除
   * @param id ノードID
   * @returns 成功したかどうか
   */
  async deleteNode(id: string): Promise<boolean> {
    const result = await this.nodeRepository.deleteNode(id);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  // =========== エッジ操作 ===========

  /**
   * エッジデータを取得する
   * @returns エッジデータの配列
   */
  async getEdges(): Promise<EdgeType[]> {
    return this.edgeRepository.getEdges();
  }

  /**
   * 指定されたIDのエッジを取得
   * @param id エッジID
   * @returns エッジデータ
   */
  async getEdge(id: string): Promise<EdgeType | null> {
    return this.edgeRepository.getEdge(id);
  }

  /**
   * 新しいエッジを追加
   * @param edgeData エッジデータ
   * @returns 成功したかどうか
   */
  async addEdge(edgeData: EdgeType): Promise<boolean> {
    const result = await this.edgeRepository.addEdge(edgeData);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  /**
   * 既存のエッジを更新
   * @param id エッジID
   * @param edgeData 更新するエッジデータ
   * @returns 成功したかどうか
   */
  async updateEdge(id: string, edgeData: Partial<EdgeType>): Promise<boolean> {
    return this.edgeRepository.updateEdge(id, edgeData);
  }

  /**
   * 指定されたIDのエッジを削除
   * @param id エッジID
   * @returns 成功したかどうか
   */
  async deleteEdge(id: string): Promise<boolean> {
    const result = await this.edgeRepository.deleteEdge(id);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  // =========== サブグラフ操作 ===========

  /**
   * サブグラフデータを取得する
   * @returns サブグラフデータの配列
   */
  async getSubgraphs(): Promise<SubgraphType[]> {
    return this.subgraphRepository.getSubgraphs();
  }

  /**
   * 指定されたIDのサブグラフを取得
   * @param id サブグラフID
   * @returns サブグラフデータ
   */
  async getSubgraph(id: string): Promise<SubgraphType | null> {
    return this.subgraphRepository.getSubgraph(id);
  }

  /**
   * 新しいサブグラフを追加
   * @param subgraphData サブグラフデータ
   * @returns 成功したかどうか
   */
  async addSubgraph(subgraphData: SubgraphType): Promise<boolean> {
    const result = await this.subgraphRepository.addSubgraph(subgraphData);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  /**
   * ノードIDの配列からサブグラフを作成
   * @param name サブグラフ名
   * @param description サブグラフの説明
   * @param nodeIds 含まれるノードのID配列
   * @returns 成功したかどうか
   */
  async createSubgraphFromNodes(
    name: string, 
    description: string, 
    nodeIds: string[]
  ): Promise<boolean> {
    const result = await this.subgraphRepository.createSubgraphFromNodes(name, description, nodeIds);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  /**
   * 既存のサブグラフを更新
   * @param id サブグラフID
   * @param subgraphData 更新するサブグラフデータ
   * @returns 成功したかどうか
   */
  async updateSubgraph(id: string, subgraphData: Partial<SubgraphType>): Promise<boolean> {
    return this.subgraphRepository.updateSubgraph(id, subgraphData);
  }

  /**
   * 指定されたIDのサブグラフを削除
   * @param id サブグラフID
   * @returns 成功したかどうか
   */
  async deleteSubgraph(id: string): Promise<boolean> {
    const result = await this.subgraphRepository.deleteSubgraph(id);
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  // =========== メタデータ操作 ===========

  /**
   * メタデータを取得する
   * @returns メタデータ
   */
  async getMetadata(): Promise<MetadataType> {
    return this.metadataRepository.getMetadata();
  }

  /**
   * メタデータを更新する
   * @param metadataData 更新するメタデータ
   * @returns 成功したかどうか
   */
  async updateMetadata(metadataData: Partial<MetadataType>): Promise<boolean> {
    return this.metadataRepository.updateMetadata(metadataData);
  }

  /**
   * グラフの統計情報を更新する
   * @returns 成功したかどうか
   */
  async updateStats(): Promise<boolean> {
    return this.metadataRepository.updateStats();
  }

  /**
   * タグを追加する
   * @param tag 追加するタグ
   * @returns 成功したかどうか
   */
  async addTag(tag: string): Promise<boolean> {
    return this.metadataRepository.addTag(tag);
  }

  /**
   * タグを削除する
   * @param tag 削除するタグ
   * @returns 成功したかどうか
   */
  async removeTag(tag: string): Promise<boolean> {
    return this.metadataRepository.removeTag(tag);
  }

  // =========== ファイル操作 ===========

  /**
   * ファイルをインポートする
   * @returns 成功したかどうか
   */
  async importFromFile(): Promise<boolean> {
    const result = await this.graphDataService.importFromFile();
    
    // 統計情報を更新
    if (result) {
      await this.metadataRepository.updateStats();
    }
    
    return result;
  }

  /**
   * ファイルをエクスポートする
   * @param type エクスポートするデータの種類
   * @returns 成功したかどうか
   */
  async exportToFile(type: ExportFileType): Promise<boolean> {
    return this.graphDataService.exportToFile(type);
  }

  /**
   * グラフデータの整合性をチェックする
   * @returns チェック結果
   */
  async validateGraphData(): Promise<GraphValidationResultType> {
    return this.graphDataService.validateGraphData();
  }

  // =========== フロントエンド構造生成 ===========

  /**
   * ノードデータを取得してフロントエンド用の階層構造を生成する
   * @returns ネスト構造のノードデータ
   */
  async getNestedStructure(): Promise<FrontendNodeType> {
    try {
      // ノードデータを取得してフロントエンド用に変換
      const nodesMap = await this.getNodes();
      console.log("getNestedStructure: ノード取得成功", Object.keys(nodesMap).length);
      
      // ノードデータから表示用のファイルノードを生成
      const fileNodes = Object.entries(nodesMap).map(([id, node]) => {
        // パスの取得方法を複数用意 (優先順位順)
        let path;
        
        // 1. メタデータ内のパスを使用
        if (node.metadata?.implementation?.location?.path) {
          path = node.metadata.implementation.location.path;
        }
        // 2. IDにパス情報が含まれている場合
        else if (id.includes(':::')) {
          path = id;
        }
        // 3. IDとノード名を組み合わせてパスを生成
        else {
          // ノード名がファイルパスっぽければそれをファイルパスとして使用
          if (node.name && (node.name.includes('/') || node.name.includes('.js') || node.name.includes('.ts'))) {
            path = `${node.name}:::${node.id}`;
          } else {
            // それ以外の場合はIDをファイルパス、ノード名を関数名とする
            path = `${id}:::${node.name}`;
          }
        }
        
        const fileNode: FileNodeType = {
          name: node.name,
          path: path
        };
        return fileNode;
      });
      
      console.log("生成されたファイルノード：", fileNodes.length, fileNodes.slice(0, 2));
      
      // ネスト構造の作成
      const result = this.nodeRepository.createNestedStructure(fileNodes);
      console.log("ネスト構造生成結果:", result.id, result.name, "子ノード数:", result.children?.length || 0);
      
      return result;
    } catch (error) {
      console.error('Failed to get nested structure:', error);
      
      // エラー時は空のノードを返す
      return { id: 'root', name: 'Error loading data', path: '' };
    }
  }

  // =========== 依存関係分析 ===========

  /**
   * 関数依存関係のデータを取得する
   * @returns 関数依存関係データ
   */
  async getFunctionDependencies(): Promise<FunctionDependencyType[]> {
    try {
      const edges = await this.getEdges();
      console.log(`getFunctionDependencies: エッジ数=${edges.length}`);
      
      // エッジのソースとターゲットが正しいか検証
      const invalidEdges = edges.filter(edge => 
        !edge.source || !edge.target || 
        typeof edge.source !== 'string' || 
        typeof edge.target !== 'string'
      );
      
      if (invalidEdges.length > 0) {
        console.warn(`警告: 無効なエッジが ${invalidEdges.length} 件あります`);
        console.warn('無効なエッジサンプル:', invalidEdges[0]);
      }
      
      // :::を含むパスを確認
      const sourcesWithSeparator = edges.filter(edge => edge.source.includes(':::')).length;
      const targetsWithSeparator = edges.filter(edge => edge.target.includes(':::')).length;
      
      console.log(`:::を含むsource: ${sourcesWithSeparator}/${edges.length}`);
      console.log(`:::を含むtarget: ${targetsWithSeparator}/${edges.length}`);
      
      // パス形式のチェックと修正
      if (sourcesWithSeparator === 0 && targetsWithSeparator === 0 && edges.length > 0) {
        console.warn('警告: エッジのソースとターゲットに:::が含まれていません。パスの形式を自動修正します。');
        
        // ノードIDからパスに変換
        const nodes = await this.getNodes();
        const nodePaths = new Map<string, string>();
        
        // ノードIDとパスのマッピングを作成（メタデータまたはID自体を使用）
        Object.entries(nodes).forEach(([id, node]) => {
          const metadataPath = node.metadata?.implementation?.location?.path;
          if (metadataPath && metadataPath.includes(':::')) {
            nodePaths.set(id, metadataPath);
          } else if (id.includes(':::')) {
            nodePaths.set(id, id);
          } else {
            // デフォルトパスを生成（ファイル名:::関数名の形式）
            nodePaths.set(id, `${id}:::${node.name}`);
          }
        });
        
        // 最初のエッジのソースとターゲットのサンプルを表示
        if (edges.length > 0) {
          const sampleEdge = edges[0];
          console.log('エッジサンプル:', {
            source: sampleEdge.source,
            sourcePath: nodePaths.get(sampleEdge.source) || 'パスなし',
            target: sampleEdge.target,
            targetPath: nodePaths.get(sampleEdge.target) || 'パスなし'
          });
        }
        
        // パスに変換したエッジを返す
        const convertedEdges = edges.map(edge => ({
          from: nodePaths.get(edge.source) || `${edge.source}:::${edge.source}`,
          to: nodePaths.get(edge.target) || `${edge.target}:::${edge.target}`
        }));
        
        console.log('パス変換後のエッジサンプル:', convertedEdges.slice(0, 2));
        return convertedEdges;
      }
      
      // エッジデータから関数依存関係を抽出（通常パターン）
      return edges.map(edge => ({
        from: edge.source,
        to: edge.target
      }));
    } catch (error) {
      console.error('Failed to get function dependencies:', error);
      return [];
    }
  }

  /**
   * 選択したノードの関連する関数を取得し、ハイライトデータを生成する
   * @param functionPath 選択された関数パス
   * @param callerDepth 呼び出し元の深さ制限
   * @param calleeDepth 呼び出し先の深さ制限
   * @returns ハイライトデータ
   */
  async getHighlightData(
    functionPath: string,
    callerDepth: number,
    calleeDepth: number
  ): Promise<HighlightDataType> {
    console.log(`getHighlightData: functionPath=${functionPath}, callerDepth=${callerDepth}, calleeDepth=${calleeDepth}`);
    
    const dependencies = await this.getFunctionDependencies();
    console.log(`依存関係データ: ${dependencies.length}件`);
    
    // 関連する関数を取得
    const relatedFunctions = this.edgeRepository.getRelatedFunctions(
      dependencies,
      functionPath,
      callerDepth,
      calleeDepth
    );
    
    console.log(`関連関数数: ${relatedFunctions.size}件`);
    if (relatedFunctions.size > 0) {
      console.log('関連関数サンプル:', Array.from(relatedFunctions).slice(0, 3));
    }
    
    // グラフ内の関連する関数だけを対象に自動ハイライトを計算
    const subgraph = dependencies.filter(
      ({ from, to }) => relatedFunctions.has(from) && relatedFunctions.has(to)
    );
    
    console.log(`フィルタリング後のサブグラフ: ${subgraph.length}件`);
    
    // 選択された関数が存在するか確認
    const pathExists = relatedFunctions.has(functionPath);
    if (!pathExists) {
      console.warn(`警告: 選択された関数 ${functionPath} が関連関数に含まれていません。ハイライト計算ができない可能性があります。`);
      
      // 近いパスがあるか探す
      const similarPaths = Array.from(relatedFunctions).filter(path => {
        // パスの部分一致をチェック
        const basePath = functionPath.split(':::')[0];
        const functionName = functionPath.split(':::')[1];
        
        return path.includes(basePath) || (functionName && path.includes(functionName));
      });
      
      if (similarPaths.length > 0) {
        console.log('類似パス候補:', similarPaths);
      }
    }
    
    // 相対位置に基づくハイライトを計算（選択された関数を基準に）
    const calculatedHighlights = this.edgeRepository.calculateRelativeHighlights(subgraph, functionPath);
    
    // フィルタリングされたハイライトデータを適用
    const filteredHighlights: HighlightDataType = {
      _minPosition: calculatedHighlights._minPosition,
      _maxPosition: calculatedHighlights._maxPosition,
      _boxCount: calculatedHighlights._boxCount
    };

    Object.entries(calculatedHighlights).forEach(([path, value]) => {
      if (!path.startsWith('_') && relatedFunctions.has(path)) {
        filteredHighlights[path] = value;
      }
    });
    
    // 選択した関数のハイライト確認
    if (filteredHighlights[functionPath] !== undefined) {
      console.log(`選択関数のハイライト位置: ${filteredHighlights[functionPath]}`);
    } else {
      console.warn(`警告: 選択関数のハイライトデータがありません`);
    }
    
    return filteredHighlights;
  }

  /**
   * ルート関数（最上位の呼び出し元）を取得する
   * @returns ルート関数の配列
   */
  async getRootFunctions(): Promise<string[]> {
    const dependencies = await this.getFunctionDependencies();
    return this.edgeRepository.findRootFunctions(dependencies);
  }

  /**
   * ツリーの最大深度を計算する
   * @param node ノード
   * @returns 最大深度
   */
  calculateMaxDepth(node: FrontendNodeType): number {
    return this.nodeRepository.calculateMaxDepth(node);
  }
}

export default NodeService;