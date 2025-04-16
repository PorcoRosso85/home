import FileSystemService from './FileSystemService';
import { 
  NodesMapType,
  EdgeType,
  SubgraphType,
  MetadataType
} from '../../types';

/**
 * グラフデータ（ノード、エッジ、サブグラフ、メタデータ）のCRUD操作を提供するサービス
 * FileSystem Access APIを使用して直接ローカルファイルを操作
 * 
 * TODO: WSL環境でのFileSystem Access API互換性の問題のため、この実装は現在使用していません。
 * 代わりにLocalStorageベースの実装が使用されています。将来的にネイティブ環境で
 * 動作させる場合は、この実装を活用できる可能性があります。
 */
class GraphDataService {
  private fileSystemService: FileSystemService;
  
  // キャッシュ
  private nodesCache: NodesMapType | null = null;
  private edgesCache: EdgeType[] | null = null;
  private subgraphsCache: SubgraphType[] | null = null;
  private metadataCache: MetadataType | null = null;
  
  // ファイル名の定数
  private static readonly NODES_FILE = 'nodes.json';
  private static readonly EDGES_FILE = 'edges.json';
  private static readonly SUBGRAPHS_FILE = 'subgraphs.json';
  private static readonly METADATA_FILE = 'metadata.json';

  constructor() {
    this.fileSystemService = new FileSystemService();
  }

  /**
   * FileSystem Access APIがサポートされているかチェック
   */
  isSupported(): boolean {
    return this.fileSystemService.isFileSystemAccessSupported();
  }

  /**
   * グラフデータを格納するディレクトリを選択
   */
  async selectGraphDirectory() {
    const result = await this.fileSystemService.selectDirectory();
    if (result) {
      // ディレクトリが選択されたら永続的なアクセス権限を要求
      await this.fileSystemService.requestPersistentAccess();
      
      // キャッシュをクリア
      this.clearCache();
    }
    return result;
  }

  /**
   * 現在選択されているディレクトリパスを取得
   */
  get currentDirectory(): string {
    return this.fileSystemService.currentDirectory;
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

  // ============= ノードCRUD操作 =============

  /**
   * ノードデータを取得
   */
  async getNodes(): Promise<NodesMapType> {
    // キャッシュがあればそれを返す
    if (this.nodesCache) {
      return this.nodesCache;
    }

    const content = await this.fileSystemService.readFile(GraphDataService.NODES_FILE);
    if (!content) {
      // ファイルが存在しない場合は空のオブジェクトを返す
      return {};
    }

    try {
      this.nodesCache = JSON.parse(content) as NodesMapType;
      return this.nodesCache;
    } catch (error) {
      console.error('Invalid JSON in nodes file:', error);
      throw new Error('Invalid JSON format in nodes file');
    }
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
    
    // ファイルに書き込み
    return this.saveNodes(nodes);
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
    
    // ファイルに書き込み
    return this.saveNodes(nodes);
  }

  /**
   * ノードデータをファイルに保存
   */
  private async saveNodes(nodes: NodesMapType): Promise<boolean> {
    const content = JSON.stringify(nodes, null, 2);
    return this.fileSystemService.writeFile(GraphDataService.NODES_FILE, content);
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

    const content = await this.fileSystemService.readFile(GraphDataService.EDGES_FILE);
    if (!content) {
      // ファイルが存在しない場合は空の配列を返す
      return [];
    }

    try {
      this.edgesCache = JSON.parse(content) as EdgeType[];
      return this.edgesCache;
    } catch (error) {
      console.error('Invalid JSON in edges file:', error);
      throw new Error('Invalid JSON format in edges file');
    }
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
    
    // ファイルに書き込み
    return this.saveEdges(edges);
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
    
    // ファイルに書き込み
    return this.saveEdges(edges);
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
    
    // ファイルに書き込み
    return this.saveEdges(edges);
  }

  /**
   * エッジデータをファイルに保存
   */
  private async saveEdges(edges: EdgeType[]): Promise<boolean> {
    const content = JSON.stringify(edges, null, 2);
    return this.fileSystemService.writeFile(GraphDataService.EDGES_FILE, content);
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

    const content = await this.fileSystemService.readFile(GraphDataService.SUBGRAPHS_FILE);
    if (!content) {
      // ファイルが存在しない場合は空の配列を返す
      return [];
    }

    try {
      this.subgraphsCache = JSON.parse(content) as SubgraphType[];
      return this.subgraphsCache;
    } catch (error) {
      console.error('Invalid JSON in subgraphs file:', error);
      throw new Error('Invalid JSON format in subgraphs file');
    }
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
    
    // ファイルに書き込み
    return this.saveSubgraphs(subgraphs);
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
    
    // ファイルに書き込み
    return this.saveSubgraphs(subgraphs);
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
    
    // ファイルに書き込み
    return this.saveSubgraphs(subgraphs);
  }

  /**
   * サブグラフデータをファイルに保存
   */
  private async saveSubgraphs(subgraphs: SubgraphType[]): Promise<boolean> {
    const content = JSON.stringify(subgraphs, null, 2);
    return this.fileSystemService.writeFile(GraphDataService.SUBGRAPHS_FILE, content);
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

    const content = await this.fileSystemService.readFile(GraphDataService.METADATA_FILE);
    if (!content) {
      // ファイルが存在しない場合はデフォルト値を返す
      return this.getDefaultMetadata();
    }

    try {
      this.metadataCache = JSON.parse(content) as MetadataType;
      return this.metadataCache;
    } catch (error) {
      console.error('Invalid JSON in metadata file:', error);
      throw new Error('Invalid JSON format in metadata file');
    }
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
    
    // ファイルに書き込み
    return this.saveMetadata(updatedMetadata);
  }

  /**
   * メタデータをファイルに保存
   */
  private async saveMetadata(metadata: MetadataType): Promise<boolean> {
    const content = JSON.stringify(metadata, null, 2);
    return this.fileSystemService.writeFile(GraphDataService.METADATA_FILE, content);
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
    const result = await this.fileSystemService.importJsonFile();
    if (!result) {
      return false;
    }

    try {
      const { name, content } = result;
      const data = JSON.parse(content);
      
      // ファイル名から種類を判断してインポート
      if (name === GraphDataService.NODES_FILE) {
        this.nodesCache = data;
        return this.saveNodes(data);
      } else if (name === GraphDataService.EDGES_FILE) {
        this.edgesCache = data;
        return this.saveEdges(data);
      } else if (name === GraphDataService.SUBGRAPHS_FILE) {
        this.subgraphsCache = data;
        return this.saveSubgraphs(data);
      } else if (name === GraphDataService.METADATA_FILE) {
        this.metadataCache = data;
        return this.saveMetadata(data);
      } else {
        throw new Error(`Unknown file type: ${name}`);
      }
    } catch (error) {
      console.error('Error importing file:', error);
      return false;
    }
  }

  /**
   * 指定された種類のデータをエクスポート
   */
  async exportToFile(type: 'nodes' | 'edges' | 'subgraphs' | 'metadata'): Promise<boolean> {
    try {
      let data: any;
      let fileName: string;
      
      // データタイプに応じてファイル名と内容を設定
      switch (type) {
        case 'nodes':
          data = await this.getNodes();
          fileName = GraphDataService.NODES_FILE;
          break;
        case 'edges':
          data = await this.getEdges();
          fileName = GraphDataService.EDGES_FILE;
          break;
        case 'subgraphs':
          data = await this.getSubgraphs();
          fileName = GraphDataService.SUBGRAPHS_FILE;
          break;
        case 'metadata':
          data = await this.getMetadata();
          fileName = GraphDataService.METADATA_FILE;
          break;
        default:
          throw new Error(`Unknown data type: ${type}`);
      }
      
      const content = JSON.stringify(data, null, 2);
      return this.fileSystemService.exportJsonFile(fileName, content);
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