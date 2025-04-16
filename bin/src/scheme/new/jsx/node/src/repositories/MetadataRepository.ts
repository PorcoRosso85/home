import { MetadataType } from '../types';
import GraphDataService from '../infrastructure/GraphDataService';

/**
 * グラフ全体のメタデータを管理するリポジトリクラス
 */
class MetadataRepository {
  private graphDataService: GraphDataService;

  constructor() {
    this.graphDataService = new GraphDataService();
  }

  /**
   * メタデータを取得する
   * @returns メタデータ
   */
  async getMetadata(): Promise<MetadataType> {
    try {
      return await this.graphDataService.getMetadata();
    } catch (error) {
      console.error('Error fetching metadata:', error);
      throw error;
    }
  }

  /**
   * メタデータを更新する
   * @param metadataData 更新するメタデータ
   * @returns 成功したかどうか
   */
  async updateMetadata(metadataData: Partial<MetadataType>): Promise<boolean> {
    try {
      return await this.graphDataService.updateMetadata(metadataData);
    } catch (error) {
      console.error('Error updating metadata:', error);
      throw error;
    }
  }

  /**
   * グラフの統計情報を更新する
   * @returns 成功したかどうか
   */
  async updateStats(): Promise<boolean> {
    try {
      return await this.graphDataService.updateStats();
    } catch (error) {
      console.error('Error updating stats:', error);
      throw error;
    }
  }

  /**
   * 新しいタグを追加する
   * @param tag 追加するタグ
   * @returns 成功したかどうか
   */
  async addTag(tag: string): Promise<boolean> {
    try {
      const metadata = await this.graphDataService.getMetadata();
      
      // タグが既に存在する場合は何もしない
      if (metadata.tags.includes(tag)) {
        return true;
      }
      
      // タグを追加
      metadata.tags.push(tag);
      
      return await this.graphDataService.updateMetadata({
        tags: metadata.tags
      });
    } catch (error) {
      console.error(`Error adding tag ${tag}:`, error);
      throw error;
    }
  }

  /**
   * タグを削除する
   * @param tag 削除するタグ
   * @returns 成功したかどうか
   */
  async removeTag(tag: string): Promise<boolean> {
    try {
      const metadata = await this.graphDataService.getMetadata();
      
      // タグが存在しない場合は何もしない
      const tagIndex = metadata.tags.indexOf(tag);
      if (tagIndex === -1) {
        return true;
      }
      
      // タグを削除
      metadata.tags.splice(tagIndex, 1);
      
      return await this.graphDataService.updateMetadata({
        tags: metadata.tags
      });
    } catch (error) {
      console.error(`Error removing tag ${tag}:`, error);
      throw error;
    }
  }

  /**
   * メタデータをエクスポートする
   * @returns 成功したかどうか
   */
  async exportMetadata(): Promise<boolean> {
    try {
      return await this.graphDataService.exportToFile('metadata');
    } catch (error) {
      console.error('Error exporting metadata:', error);
      throw error;
    }
  }
}

export default MetadataRepository;