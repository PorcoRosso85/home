import LocalStorageService from './LocalStorageService';
import { 
  NodesMapType,
  EdgeType,
  SubgraphType,
  MetadataType
} from '../types';

/**
 * グラフデータ（ノード、エッジ、サブグラフ、メタデータ）のCRUD操作を提供するサービス
 * LocalStorageを使用してJSONデータを保持し、ブラウザで永続化する
 */
class GraphDataService {
  private localStorageService: LocalStorageService;
  
  // キャッシュ
  private nodesCache: NodesMapType | null = null;
  private edgesCache: EdgeType[] | null = null;
  private subgraphsCache: SubgraphType[] | null = null;
  private metadataCache: MetadataType | null = null;
  
  // ストレージキーの定数
  private static readonly NODES_KEY = 'nodes';
  private static readonly EDGES_KEY = 'edges';
  private static readonly SUBGRAPHS_KEY = 'subgraphs';
  private static readonly METADATA_KEY = 'metadata';
  private static readonly DATA_LOADED_KEY = 'data_loaded';

  // ファイル名の定数（エクスポート用）
  private static readonly NODES_FILE = 'nodes.json';
  private static readonly EDGES_FILE = 'edges.json';
  private static readonly SUBGRAPHS_FILE = 'subgraphs.json';
  private static readonly METADATA_FILE = 'metadata.json';

  constructor() {
    this.localStorageService = new LocalStorageService();
    this.initializeFromPublicFiles();
  }

  private async initializeFromPublicFiles(): Promise<void> {
    // NOTE: LocalStorageの使用をいったんコメントアウト
    // すでにデータが読み込まれているかチェック
    /*
    const dataLoaded = this.localStorageService.loadData<boolean>(GraphDataService.DATA_LOADED_KEY);
    if (dataLoaded) {
      // 各キャッシュを初期化
      this.loadFromLocalStorage();
      console.log("既存のデータをLocalStorageから読み込みました");
      
      // キャッシュを確認し、デバッグ情報を出力
      const nodesCache = this.localStorageService.loadData<NodesMapType>(GraphDataService.NODES_KEY);
      if (nodesCache) {
        const nodeCount = Object.keys(nodesCache).length;
        console.log(`LocalStorageから読み込んだノード数: ${nodeCount}`);
        if (nodeCount > 0) {
          // サンプルのノードを表示
          const sampleNodeKeys = Object.keys(nodesCache).slice(0, 2);
          console.log("ノードサンプル:", sampleNodeKeys);
          
          // ノードにパス情報があるか確認
          const nodesWithPath = Object.values(nodesCache).filter(
            node => node.metadata?.implementation?.location?.path
          ).length;
          console.log(`メタデータにパス情報を持つノード数: ${nodesWithPath}/${nodeCount}`);
        }
      }
      return;
    }
    */
    
    // NOTE: 常に公開ファイルから読み込むように変更

    try {
      console.log("公開ファイルからデータ読み込みを試みます...");
      
      // パスのバリアントを用意
      const paths = [
        './public/nodes.json',
        '/public/nodes.json',
        '../graph/db/nodes.json',
        '/home/nixos/scheme/new/jsx/graph/db/nodes.json'
      ];
      
      // nodesの読み込み（複数のパスを試行）
      let nodesResponse = null;
      let loadedPath = '';
      
      for (const path of paths) {
        try {
          console.log(`${path} の読み込みを試みます...`);
          const response = await fetch(path);
          if (response.ok) {
            nodesResponse = response;
            loadedPath = path;
            break;
          }
        } catch (e) {
          console.log(`${path} からの読み込みに失敗: ${e.message}`);
        }
      }
      
      if (nodesResponse && nodesResponse.ok) {
        const nodes = await nodesResponse.json();
        this.nodesCache = nodes;
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.NODES_KEY, nodes);
        console.log(`${loadedPath} を正常に読み込みました (ノード数: ${Object.keys(nodes).length})`);
        
        // ノードのパス情報をチェック
        if (Object.keys(nodes).length > 0) {
          const sampleNode = Object.values(nodes)[0];
          console.log("最初のノードサンプル:", {
            id: sampleNode.id,
            name: sampleNode.name,
            path: sampleNode.metadata?.implementation?.location?.path || 'パス情報なし'
          });
        }
      } else {
        console.error(`nodes.json の取得に失敗しました`);
        
        // 他のパスを試みる (最後の手段としてハードコードされたパス)
        try {
          const directPath = '/home/nixos/scheme/new/jsx/graph/db/nodes.json';
          const directContent = await (await fetch(directPath)).text();
          if (directContent) {
            const nodes = JSON.parse(directContent);
            this.nodesCache = nodes;
            // NOTE: LocalStorage保存をコメントアウト
            // this.localStorageService.saveData(GraphDataService.NODES_KEY, nodes);
            console.log(`${directPath} から直接読み込みに成功しました`);
          }
        } catch (directError) {
          console.error("直接パスからの読み込みにも失敗:", directError);
        }
      }

      // ベースディレクトリのパスバリエーション（末尾のスラッシュなし）
      const basePaths = [
        './public',
        '/public',
        '../graph/db',
        '/home/nixos/scheme/new/jsx/graph/db'
      ];
      
      // ファイルの読み込みを行う汎用関数
      const loadJsonFile = async (fileName: string): Promise<any> => {
        for (const basePath of basePaths) {
          try {
            const fullPath = `${basePath}/${fileName}`;
            console.log(`${fullPath} の読み込みを試みます...`);
            const response = await fetch(fullPath);
            if (response.ok) {
              const data = await response.json();
              console.log(`${fullPath} を正常に読み込みました`);
              return { data, path: fullPath };
            }
          } catch (e) {
            console.log(`${fileName} 読み込み失敗 (${e.message})`);
          }
        }
        console.error(`${fileName} の読み込みに失敗しました`);
        return { data: null, path: '' };
      };
      
      // edgesの読み込み
      const { data: edges, path: edgesPath } = await loadJsonFile('edges.json');
      if (edges) {
        this.edgesCache = edges;
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.EDGES_KEY, edges);
        console.log(`edges.json を正常に読み込みました (エッジ数: ${edges.length})`);
      } else {
        // エッジがない場合は空の配列を設定
        this.edgesCache = [];
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.EDGES_KEY, []);
      }

      // subgraphsの読み込み
      const { data: subgraphs, path: subgraphsPath } = await loadJsonFile('subgraphs.json');
      if (subgraphs) {
        this.subgraphsCache = subgraphs;
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, subgraphs);
        console.log(`subgraphs.json を正常に読み込みました (サブグラフ数: ${subgraphs.length})`);
      } else {
        // サブグラフがない場合は空の配列を設定
        this.subgraphsCache = [];
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, []);
      }

      // metadataの読み込み
      const { data: metadata, path: metadataPath } = await loadJsonFile('metadata.json');
      if (metadata) {
        this.metadataCache = metadata;
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.METADATA_KEY, metadata);
        console.log("metadata.json を正常に読み込みました");
      } else {
        // メタデータがない場合はデフォルト値を設定
        const defaultMetadata = this.getDefaultMetadata();
        this.metadataCache = defaultMetadata;
        // NOTE: LocalStorage保存をコメントアウト
        // this.localStorageService.saveData(GraphDataService.METADATA_KEY, defaultMetadata);
        console.log("デフォルトのメタデータを設定しました");
      }

      // データ読み込み完了フラグを設定
      // NOTE: LocalStorage保存をコメントアウト
      // this.localStorageService.saveData(GraphDataService.DATA_LOADED_KEY, true);
      
      // データの整合性チェック
      const nodeCount = Object.keys(this.nodesCache || {}).length;
      const edgesCount = (this.edgesCache || []).length;
      const subgraphsCount = (this.subgraphsCache || []).length;
      
      console.log(`データ読み込み完了: ノード数=${nodeCount}, エッジ数=${edgesCount}, サブグラフ数=${subgraphsCount}`);
      
      // 少なくともノードデータがあるか確認
      if (nodeCount === 0) {
        console.warn("警告: ノードデータが読み込まれませんでした。公開ディレクトリのパスを確認してください。");
      }
    } catch (error) {
      console.error('Error initializing data from public files:', error);
      if (error instanceof Error) {
        console.error(`
ファイル読み込みに失敗しました。以下をご確認ください:
1. ファイルパス: ./public/*.json
2. サーバー設定: 静的ファイルが正しく配信されているか
3. CORS設定: クロスオリジンリクエストが許可されているか
4. ファイル形式: JSONファイルが有効な形式か
5. 関数情報: ファイルパス:::関数名 の形式が正しいか

エラー詳細: ${error.message}
スタックトレース: ${error.stack}
`);
      }
    }
  }

  /**
   * LocalStorageから各キャッシュを初期化
   */
  private loadFromLocalStorage(): void {
    this.nodesCache = this.localStorageService.loadData<NodesMapType>(GraphDataService.NODES_KEY) || {};
    this.edgesCache = this.localStorageService.loadData<EdgeType[]>(GraphDataService.EDGES_KEY) || [];
    this.subgraphsCache = this.localStorageService.loadData<SubgraphType[]>(GraphDataService.SUBGRAPHS_KEY) || [];
    this.metadataCache = this.localStorageService.loadData<MetadataType>(GraphDataService.METADATA_KEY) || this.getDefaultMetadata();
  }

  /**
   * キャッシュをクリア
   */
  clearCache(): void {
    this.nodesCache = null;
    this.edgesCache = null;
    this.subgraphsCache = null;
    this.metadataCache = null;
  }

  /**
   * すべてのデータをリセット（LocalStorageからクリア）
   */
  async resetAllData(): Promise<boolean> {
    this.clearCache();
    const result = this.localStorageService.clearAllData();
    
    // データ読み込み完了フラグをリセット
    if (result) {
      this.localStorageService.removeData(GraphDataService.DATA_LOADED_KEY);
      // 公開ファイルから再初期化
      await this.initializeFromPublicFiles();
    }
    
    return result;
  }

  /**
   * LocalStorageの使用状況を取得
   */
  getStorageInfo(): { used: number; total: number; percentage: number } {
    return this.localStorageService.getStorageInfo();
  }

  // ============= ノードCRUD操作 =============

  /**
   * ノードデータを取得
   */
  async getNodes(): Promise<NodesMapType> {
    // キャッシュがあればそれを返す
    if (this.nodesCache) {
      return this.nodesCache;
    }

    // LocalStorageから読み込み
    const nodes = this.localStorageService.loadData<NodesMapType>(GraphDataService.NODES_KEY);
    if (nodes) {
      this.nodesCache = nodes;
      return nodes;
    }

    // データがない場合は空のオブジェクトを返す
    return {};
  }

  /**
   * 指定されたIDのノードを取得
   */
  async getNode(id: string) {
    const nodes = await this.getNodes();
    return nodes[id] || null;
  }

  /**
   * 新しいノードを追加または既存のノードを更新
   */
  async saveNode(id: string, nodeData: any): Promise<boolean> {
    const nodes = await this.getNodes();
    
    // 既存のノードを更新または新規作成
    nodes[id] = {
      ...nodeData,
      id // IDが一致することを保証
    };
    
    // キャッシュを更新
    this.nodesCache = nodes;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.NODES_KEY, nodes);
  }

  /**
   * 指定されたIDのノードを削除
   */
  async deleteNode(id: string): Promise<boolean> {
    const nodes = await this.getNodes();
    
    // ノードが存在しなければfalseを返す
    if (!nodes[id]) {
      return false;
    }
    
    // ノードを削除
    delete nodes[id];
    
    // キャッシュを更新
    this.nodesCache = nodes;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.NODES_KEY, nodes);
  }

  /**
   * ノードデータをダウンロード
   */
  async downloadNodes(): Promise<void> {
    const nodes = await this.getNodes();
    this.localStorageService.downloadJson(GraphDataService.NODES_FILE, nodes);
  }

  // ============= エッジCRUD操作 =============

  /**
   * エッジデータを取得
   */
  async getEdges(): Promise<EdgeType[]> {
    // キャッシュがあればそれを返す
    if (this.edgesCache) {
      return this.edgesCache;
    }

    // LocalStorageから読み込み
    const edges = this.localStorageService.loadData<EdgeType[]>(GraphDataService.EDGES_KEY);
    if (edges) {
      this.edgesCache = edges;
      return edges;
    }

    // データがない場合は空の配列を返す
    return [];
  }

  /**
   * 指定されたIDのエッジを取得
   */
  async getEdge(id: string) {
    const edges = await this.getEdges();
    return edges.find(edge => edge.id === id) || null;
  }

  /**
   * 新しいエッジを追加
   */
  async addEdge(edgeData: EdgeType): Promise<boolean> {
    const edges = await this.getEdges();
    
    // IDが重複していないか確認
    if (edges.some(edge => edge.id === edgeData.id)) {
      throw new Error(`Edge with ID ${edgeData.id} already exists`);
    }
    
    // エッジを追加
    edges.push(edgeData);
    
    // キャッシュを更新
    this.edgesCache = edges;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.EDGES_KEY, edges);
  }

  /**
   * 既存のエッジを更新
   */
  async updateEdge(id: string, edgeData: Partial<EdgeType>): Promise<boolean> {
    const edges = await this.getEdges();
    
    // 更新対象のエッジのインデックスを検索
    const index = edges.findIndex(edge => edge.id === id);
    if (index === -1) {
      throw new Error(`Edge with ID ${id} not found`);
    }
    
    // エッジを更新
    edges[index] = {
      ...edges[index],
      ...edgeData,
      id // IDが変更されないことを保証
    };
    
    // キャッシュを更新
    this.edgesCache = edges;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.EDGES_KEY, edges);
  }

  /**
   * 指定されたIDのエッジを削除
   */
  async deleteEdge(id: string): Promise<boolean> {
    const edges = await this.getEdges();
    
    // 削除対象のエッジのインデックスを検索
    const index = edges.findIndex(edge => edge.id === id);
    if (index === -1) {
      return false; // エッジが見つからない
    }
    
    // エッジを削除
    edges.splice(index, 1);
    
    // キャッシュを更新
    this.edgesCache = edges;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.EDGES_KEY, edges);
  }

  /**
   * エッジデータをダウンロード
   */
  async downloadEdges(): Promise<void> {
    const edges = await this.getEdges();
    this.localStorageService.downloadJson(GraphDataService.EDGES_FILE, edges);
  }

  // ============= サブグラフCRUD操作 =============

  /**
   * サブグラフデータを取得
   */
  async getSubgraphs(): Promise<SubgraphType[]> {
    // キャッシュがあればそれを返す
    if (this.subgraphsCache) {
      return this.subgraphsCache;
    }

    // LocalStorageから読み込み
    const subgraphs = this.localStorageService.loadData<SubgraphType[]>(GraphDataService.SUBGRAPHS_KEY);
    if (subgraphs) {
      this.subgraphsCache = subgraphs;
      return subgraphs;
    }

    // データがない場合は空の配列を返す
    return [];
  }

  /**
   * 指定されたIDのサブグラフを取得
   */
  async getSubgraph(id: string) {
    const subgraphs = await this.getSubgraphs();
    return subgraphs.find(subgraph => subgraph.id === id) || null;
  }

  /**
   * 新しいサブグラフを追加
   */
  async addSubgraph(subgraphData: SubgraphType): Promise<boolean> {
    const subgraphs = await this.getSubgraphs();
    
    // IDが重複していないか確認
    if (subgraphs.some(subgraph => subgraph.id === subgraphData.id)) {
      throw new Error(`Subgraph with ID ${subgraphData.id} already exists`);
    }
    
    // サブグラフを追加
    subgraphs.push(subgraphData);
    
    // キャッシュを更新
    this.subgraphsCache = subgraphs;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, subgraphs);
  }

  /**
   * 既存のサブグラフを更新
   */
  async updateSubgraph(id: string, subgraphData: Partial<SubgraphType>): Promise<boolean> {
    const subgraphs = await this.getSubgraphs();
    
    // 更新対象のサブグラフのインデックスを検索
    const index = subgraphs.findIndex(subgraph => subgraph.id === id);
    if (index === -1) {
      throw new Error(`Subgraph with ID ${id} not found`);
    }
    
    // サブグラフを更新
    subgraphs[index] = {
      ...subgraphs[index],
      ...subgraphData,
      id // IDが変更されないことを保証
    };
    
    // キャッシュを更新
    this.subgraphsCache = subgraphs;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, subgraphs);
  }

  /**
   * 指定されたIDのサブグラフを削除
   */
  async deleteSubgraph(id: string): Promise<boolean> {
    const subgraphs = await this.getSubgraphs();
    
    // 削除対象のサブグラフのインデックスを検索
    const index = subgraphs.findIndex(subgraph => subgraph.id === id);
    if (index === -1) {
      return false; // サブグラフが見つからない
    }
    
    // サブグラフを削除
    subgraphs.splice(index, 1);
    
    // キャッシュを更新
    this.subgraphsCache = subgraphs;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, subgraphs);
  }

  /**
   * サブグラフデータをダウンロード
   */
  async downloadSubgraphs(): Promise<void> {
    const subgraphs = await this.getSubgraphs();
    this.localStorageService.downloadJson(GraphDataService.SUBGRAPHS_FILE, subgraphs);
  }

  // ============= メタデータCRUD操作 =============

  /**
   * メタデータを取得
   */
  async getMetadata(): Promise<MetadataType> {
    // キャッシュがあればそれを返す
    if (this.metadataCache) {
      return this.metadataCache;
    }

    // LocalStorageから読み込み
    const metadata = this.localStorageService.loadData<MetadataType>(GraphDataService.METADATA_KEY);
    if (metadata) {
      this.metadataCache = metadata;
      return metadata;
    }

    // データがない場合はデフォルト値を返す
    const defaultMetadata = this.getDefaultMetadata();
    this.metadataCache = defaultMetadata;
    return defaultMetadata;
  }

  /**
   * デフォルトのメタデータを取得
   */
  private getDefaultMetadata(): MetadataType {
    return {
      version: '1.0.0',
      lastUpdated: new Date().toISOString(),
      author: 'システム',
      description: 'グラフ定義',
      stats: {
        nodeCount: 0,
        edgeCount: 0,
        subgraphCount: 0
      },
      statusSummary: {},
      tags: []
    };
  }

  /**
   * メタデータを更新
   */
  async updateMetadata(metadataData: Partial<MetadataType>): Promise<boolean> {
    // 現在のメタデータを取得
    const metadata = await this.getMetadata();
    
    // メタデータを更新
    const updatedMetadata = {
      ...metadata,
      ...metadataData,
      // 最終更新日時を現在の時刻に設定
      lastUpdated: new Date().toISOString()
    };
    
    // キャッシュを更新
    this.metadataCache = updatedMetadata;
    
    // LocalStorageに保存
    return this.localStorageService.saveData(GraphDataService.METADATA_KEY, updatedMetadata);
  }

  /**
   * メタデータをダウンロード
   */
  async downloadMetadata(): Promise<void> {
    const metadata = await this.getMetadata();
    this.localStorageService.downloadJson(GraphDataService.METADATA_FILE, metadata);
  }

  /**
   * グラフの統計情報を更新
   */
  async updateStats(): Promise<boolean> {
    // 各データを取得
    const nodes = await this.getNodes();
    const edges = await this.getEdges();
    const subgraphs = await this.getSubgraphs();
    
    // ステータスの集計
    const statusCounts: Record<string, number> = {};
    Object.values(nodes).forEach(node => {
      const status = node.metadata?.implementation?.status;
      if (status) {
        statusCounts[status] = (statusCounts[status] || 0) + 1;
      }
    });
    
    // メタデータを更新
    return this.updateMetadata({
      stats: {
        nodeCount: Object.keys(nodes).length,
        edgeCount: edges.length,
        subgraphCount: subgraphs.length
      },
      statusSummary: statusCounts
    });
  }

  // ============= ファイル操作 =============

  /**
   * 指定されたJSONファイルをインポート
   */
  async importFromFile(): Promise<boolean> {
    const result = await this.localStorageService.loadJsonFromFile();
    if (!result) {
      return false;
    }

    try {
      const { name, content } = result;
      
      // ファイル名から種類を判断してインポート
      if (name === GraphDataService.NODES_FILE) {
        this.nodesCache = content;
        return this.localStorageService.saveData(GraphDataService.NODES_KEY, content);
      } else if (name === GraphDataService.EDGES_FILE) {
        this.edgesCache = content;
        return this.localStorageService.saveData(GraphDataService.EDGES_KEY, content);
      } else if (name === GraphDataService.SUBGRAPHS_FILE) {
        this.subgraphsCache = content;
        return this.localStorageService.saveData(GraphDataService.SUBGRAPHS_KEY, content);
      } else if (name === GraphDataService.METADATA_FILE) {
        this.metadataCache = content;
        return this.localStorageService.saveData(GraphDataService.METADATA_KEY, content);
      } else {
        throw new Error(`Unknown file type: ${name}`);
      }
    } catch (error) {
      console.error('Error importing file:', error);
      return false;
    }
  }

  /**
   * 指定された種類のデータをダウンロード
   */
  async exportToFile(type: 'nodes' | 'edges' | 'subgraphs' | 'metadata'): Promise<boolean> {
    try {
      switch (type) {
        case 'nodes':
          await this.downloadNodes();
          break;
        case 'edges':
          await this.downloadEdges();
          break;
        case 'subgraphs':
          await this.downloadSubgraphs();
          break;
        case 'metadata':
          await this.downloadMetadata();
          break;
        default:
          throw new Error(`Unknown data type: ${type}`);
      }
      return true;
    } catch (error) {
      console.error('Error exporting file:', error);
      return false;
    }
  }

  /**
   * データの整合性チェック
   */
  async validateGraphData(): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];
    
    try {
      // ノードとエッジを取得
      const nodes = await this.getNodes();
      const edges = await this.getEdges();
      
      // 1. すべてのエッジのソースとターゲットノードが存在するか確認
      edges.forEach(edge => {
        if (!nodes[edge.source]) {
          errors.push(`Edge ${edge.id}: Source node '${edge.source}' does not exist`);
        }
        if (!nodes[edge.target]) {
          errors.push(`Edge ${edge.id}: Target node '${edge.target}' does not exist`);
        }
      });
      
      // 2. 必須フィールドが存在するか確認
      Object.entries(nodes).forEach(([id, node]) => {
        if (!node.name) errors.push(`Node ${id}: Missing required field 'name'`);
        if (!node.type) errors.push(`Node ${id}: Missing required field 'type'`);
        if (!node.description) errors.push(`Node ${id}: Missing required field 'description'`);
      });
      
      edges.forEach(edge => {
        if (!edge.name) errors.push(`Edge ${edge.id}: Missing required field 'name'`);
        if (!edge.description) errors.push(`Edge ${edge.id}: Missing required field 'description'`);
      });
      
      return { valid: errors.length === 0, errors };
    } catch (error) {
      console.error('Error validating graph data:', error);
      return { valid: false, errors: [(error as Error).message] };
    }
  }
}

export default GraphDataService;