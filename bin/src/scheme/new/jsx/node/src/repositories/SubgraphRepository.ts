import { SubgraphType } from '../types';
import GraphDataService from '../infrastructure/GraphDataService';

/**
 * サブグラフデータを管理するリポジトリクラス
 */
class SubgraphRepository {
  private graphDataService: GraphDataService;

  constructor() {
    this.graphDataService = new GraphDataService();
  }

  /**
   * サブグラフデータを取得する
   * @returns サブグラフデータの配列
   */
  async getSubgraphs(): Promise<SubgraphType[]> {
    try {
      return await this.graphDataService.getSubgraphs();
    } catch (error) {
      console.error('Error fetching subgraphs:', error);
      throw error;
    }
  }

  /**
   * 指定されたIDのサブグラフを取得
   * @param id サブグラフID
   * @returns サブグラフデータ
   */
  async getSubgraph(id: string) {
    try {
      return await this.graphDataService.getSubgraph(id);
    } catch (error) {
      console.error(`Error fetching subgraph ${id}:`, error);
      throw error;
    }
  }

  /**
   * 新しいサブグラフを追加
   * @param subgraphData サブグラフデータ
   * @returns 成功したかどうか
   */
  async addSubgraph(subgraphData: SubgraphType): Promise<boolean> {
    try {
      return await this.graphDataService.addSubgraph(subgraphData);
    } catch (error) {
      console.error(`Error adding subgraph:`, error);
      throw error;
    }
  }

  /**
   * 既存のサブグラフを更新
   * @param id サブグラフID
   * @param subgraphData 更新するサブグラフデータ
   * @returns 成功したかどうか
   */
  async updateSubgraph(id: string, subgraphData: Partial<SubgraphType>): Promise<boolean> {
    try {
      return await this.graphDataService.updateSubgraph(id, subgraphData);
    } catch (error) {
      console.error(`Error updating subgraph ${id}:`, error);
      throw error;
    }
  }

  /**
   * 指定されたIDのサブグラフを削除
   * @param id サブグラフID
   * @returns 成功したかどうか
   */
  async deleteSubgraph(id: string): Promise<boolean> {
    try {
      return await this.graphDataService.deleteSubgraph(id);
    } catch (error) {
      console.error(`Error deleting subgraph ${id}:`, error);
      throw error;
    }
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
    try {
      // 新しいサブグラフIDを生成
      const id = this.generateSubgraphId(name);
      
      // サブグラフデータを作成
      const subgraphData: SubgraphType = {
        id,
        name,
        description,
        nodeIds,
        metadata: {
          implementation: {
            status: '開発中',
            progress: 0
          }
        },
        tags: []
      };
      
      // サブグラフを追加
      return await this.graphDataService.addSubgraph(subgraphData);
    } catch (error) {
      console.error('Error creating subgraph from nodes:', error);
      throw error;
    }
  }

  /**
   * サブグラフ名からIDを生成
   * @param name サブグラフ名
   * @returns 生成されたID
   */
  private generateSubgraphId(name: string): string {
    // 名前からIDを生成（英数字とハイフンのみ）
    return name
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }
}

export default SubgraphRepository;