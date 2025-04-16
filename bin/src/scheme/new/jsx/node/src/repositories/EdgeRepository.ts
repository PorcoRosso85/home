import { EdgesArrayType, HighlightDataType } from '../types';
import GraphDataService from '../infrastructure/GraphDataService';

/**
 * エッジデータを管理するリポジトリクラス
 */
class EdgeRepository {
  private graphDataService: GraphDataService;

  constructor() {
    this.graphDataService = new GraphDataService();
  }

  /**
   * エッジデータを取得する
   * @returns エッジデータの配列
   */
  async getEdges(): Promise<EdgesArrayType> {
    try {
      return await this.graphDataService.getEdges();
    } catch (error) {
      console.error('Error fetching edges:', error);
      throw error;
    }
  }

  /**
   * 指定されたIDのエッジを取得
   * @param id エッジID
   * @returns エッジデータ
   */
  async getEdge(id: string) {
    try {
      return await this.graphDataService.getEdge(id);
    } catch (error) {
      console.error(`Error fetching edge ${id}:`, error);
      throw error;
    }
  }

  /**
   * 新しいエッジを追加
   * @param edgeData エッジデータ
   * @returns 成功したかどうか
   */
  async addEdge(edgeData: any): Promise<boolean> {
    try {
      return await this.graphDataService.addEdge(edgeData);
    } catch (error) {
      console.error(`Error adding edge:`, error);
      throw error;
    }
  }

  /**
   * 既存のエッジを更新
   * @param id エッジID
   * @param edgeData 更新するエッジデータ
   * @returns 成功したかどうか
   */
  async updateEdge(id: string, edgeData: any): Promise<boolean> {
    try {
      return await this.graphDataService.updateEdge(id, edgeData);
    } catch (error) {
      console.error(`Error updating edge ${id}:`, error);
      throw error;
    }
  }

  /**
   * 指定されたIDのエッジを削除
   * @param id エッジID
   * @returns 成功したかどうか
   */
  async deleteEdge(id: string): Promise<boolean> {
    try {
      return await this.graphDataService.deleteEdge(id);
    } catch (error) {
      console.error(`Error deleting edge ${id}:`, error);
      throw error;
    }
  }

  /**
   * 依存関係から相対的なハイライトデータを計算する
   * @param dependencies 依存関係の配列
   * @param selectedPath 選択された関数パス
   * @returns ハイライトデータ
   */
  calculateRelativeHighlights(
    dependencies: Array<{ from: string; to: string }>, 
    selectedPath: string
  ): HighlightDataType {
    // グラフを構築
    const graph = new Map<string, string[]>();
    const inDegree = new Map<string, number>(); // 入次数（依存される数）を追跡
    
    // すべてのノードを初期化
    dependencies.forEach(({ from, to }) => {
      if (!graph.has(from)) {
        graph.set(from, []);
        inDegree.set(from, 0);
      }
      if (!graph.has(to)) {
        graph.set(to, []);
        inDegree.set(to, 0);
      }
    });
    
    // エッジを追加し、入次数を計算
    dependencies.forEach(({ from, to }) => {
      const neighbors = graph.get(from);
      if (neighbors) {
        neighbors.push(to);
      }
      inDegree.set(to, (inDegree.get(to) || 0) + 1);
    });
    
    // 入次数が0のノード（呼び出し元関数）を見つける
    const queue = Array.from(graph.keys()).filter(node => inDegree.get(node) === 0);
    
    // トポロジカルソートの結果
    const sortedNodes: string[] = [];
    
    // 幅優先探索でトポロジカルソート
    while (queue.length > 0) {
      const node = queue.shift();
      if (node) {
        sortedNodes.push(node);
        
        const neighbors = graph.get(node) || [];
        for (const neighbor of neighbors) {
          const currentInDegree = inDegree.get(neighbor);
          if (currentInDegree !== undefined) {
            inDegree.set(neighbor, currentInDegree - 1);
            if (currentInDegree - 1 === 0) {
              queue.push(neighbor);
            }
          }
        }
      }
    }
    
    // 選択された関数のインデックスを見つける
    const selectedIndex = sortedNodes.indexOf(selectedPath);
    
    // ハイライトデータを計算
    const highlightData: HighlightDataType = {
      _minPosition: 0,
      _maxPosition: 0,
      _boxCount: 0
    };
    
    // 相対位置の最小値と最大値を追跡
    let minRelativePosition = 0;
    let maxRelativePosition = 0;
    
    // 選択関数を基準とした相対位置に基づいてボックス番号を割り当て
    sortedNodes.forEach((node, index) => {
      // 相対位置を計算（選択関数からの距離）
      const relativePosition = index - selectedIndex;
      highlightData[node] = relativePosition;
      
      // 最小値と最大値を更新
      minRelativePosition = Math.min(minRelativePosition, relativePosition);
      maxRelativePosition = Math.max(maxRelativePosition, relativePosition);
    });
    
    // 実際に使用されるボックス数と範囲情報を追加
    highlightData._minPosition = minRelativePosition;
    highlightData._maxPosition = maxRelativePosition;
    highlightData._boxCount = maxRelativePosition - minRelativePosition + 1;
    
    return highlightData;
  }

  /**
   * 依存関係から関数の関連ノードを取得する
   * @param dependencies 依存関係の配列
   * @param functionPath 関数パス
   * @param callerDepth 呼び出し元の深さ制限
   * @param calleeDepth 呼び出し先の深さ制限
   * @returns 関連する関数のセット
   */
  getRelatedFunctions(
    dependencies: Array<{ from: string; to: string }>,
    functionPath: string,
    callerDepth: number,
    calleeDepth: number
  ): Set<string> {
    const relatedFunctions = new Set<string>();
    
    // 選択した関数を起点とする依存関係を追加（呼び出し先）
    const findDependencies = (
      funcPath: string, 
      currentDepth = 0, 
      visitedPaths = new Set<string>()
    ): void => {
      if (visitedPaths.has(funcPath) || currentDepth > calleeDepth) return; // 循環依存または深さ制限
      visitedPaths.add(funcPath);
      relatedFunctions.add(funcPath);
      
      // この関数が呼び出す他の関数を探す
      dependencies.forEach(({ from, to }) => {
        if (from === funcPath) {
          relatedFunctions.add(to);
          findDependencies(to, currentDepth + 1, visitedPaths);
        }
      });
    };
    
    // 選択した関数を呼び出す関数を探す関数（呼び出し元）
    const findCallers = (
      funcPath: string, 
      currentDepth = 0, 
      visitedPaths = new Set<string>()
    ): void => {
      if (visitedPaths.has(funcPath) || currentDepth > callerDepth) return; // 循環依存または深さ制限
      visitedPaths.add(funcPath);
      relatedFunctions.add(funcPath);
      
      // この関数を呼び出す他の関数を探す
      dependencies.forEach(({ from, to }) => {
        if (to === funcPath) {
          relatedFunctions.add(from);
          findCallers(from, currentDepth + 1, visitedPaths);
        }
      });
    };
    
    // 選択した関数の依存関係をすべて調べる（深さ制限付き）
    findDependencies(functionPath, 0, new Set<string>());
    findCallers(functionPath, 0, new Set<string>());
    
    return relatedFunctions;
  }

  /**
   * ルート関数（最上位の呼び出し元）を見つける
   * @param dependencies 依存関係の配列
   * @returns ルート関数の配列
   */
  findRootFunctions(dependencies: Array<{ from: string; to: string }>): string[] {
    const graph = new Map<string, string[]>();
    const inDegree = new Map<string, number>();
    
    // グラフを構築
    dependencies.forEach(({ from, to }) => {
      if (!graph.has(from)) graph.set(from, []);
      if (!graph.has(to)) graph.set(to, []);
      
      const neighbors = graph.get(from);
      if (neighbors) {
        neighbors.push(to);
      }
      inDegree.set(to, (inDegree.get(to) || 0) + 1);
      if (!inDegree.has(from)) inDegree.set(from, 0);
    });
    
    // 入次数が0のノード（呼び出し元関数）を見つける
    return Array.from(graph.keys()).filter(node => inDegree.get(node) === 0);
  }
}

export default EdgeRepository;