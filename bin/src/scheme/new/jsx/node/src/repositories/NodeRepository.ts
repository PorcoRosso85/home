import { NodesMapType, FrontendNodeType, FileNodeType } from '../types';
import GraphDataService from '../infrastructure/GraphDataService';

/**
 * ノードデータを管理するリポジトリクラス
 */
class NodeRepository {
  private graphDataService: GraphDataService;

  constructor() {
    this.graphDataService = new GraphDataService();
  }

  /**
   * ノードデータを取得する
   * @returns ノードデータのマップ
   */
  async getNodes(): Promise<NodesMapType> {
    try {
      const nodes = await this.graphDataService.getNodes();
      
      // 関数情報の存在チェック
      // ノードが存在しない場合はエラーを投げる
      if (Object.keys(nodes).length === 0) {
        throw new Error('ファイル内に関数情報が見つかりません。少なくとも1つの関数が必要です。');
      }
      
      // 少なくとも1つの関数型ノードが含まれていることを確認
      // 関数型ノードは implementation.location.path に ::: を含むか、id自体に:::を含む
      const functionNodes = Object.values(nodes).filter(node => {
        // 1. メタデータ内のlocation.pathをチェック
        const locationPath = node.metadata?.implementation?.location?.path;
        if (locationPath && typeof locationPath === 'string' && locationPath.includes(':::')) {
          return true;
        }
        
        // 2. IDで関数パスをチェック
        if (node.id && typeof node.id === 'string' && node.id.includes(':::')) {
          return true;
        }
        
        // 3. nameにファイル名のパターンが含まれているかチェック
        if (node.name && typeof node.name === 'string' && (node.name.includes('/') || node.name.includes('.js') || node.name.includes('.ts'))) {
          return true;
        }
        
        return false;
      });
      
      if (functionNodes.length === 0) {
        console.warn('関数情報が正しくパースされていません。metadata.implementation.location.path または id に最低一つの関数情報（:::を含むパス）が必要です。');
      }
      
      return nodes;
    } catch (error) {
      console.error('Error fetching nodes:', error);
      throw error;
    }
  }

  /**
   * 指定されたIDのノードを取得
   * @param id ノードID
   * @returns ノードデータ
   */
  async getNode(id: string) {
    try {
      return await this.graphDataService.getNode(id);
    } catch (error) {
      console.error(`Error fetching node ${id}:`, error);
      throw error;
    }
  }

  /**
   * 新しいノードを追加または既存のノードを更新
   * @param id ノードID
   * @param nodeData ノードデータ
   * @returns 成功したかどうか
   */
  async saveNode(id: string, nodeData: any): Promise<boolean> {
    try {
      return await this.graphDataService.saveNode(id, nodeData);
    } catch (error) {
      console.error(`Error saving node ${id}:`, error);
      throw error;
    }
  }

  /**
   * 指定されたIDのノードを削除
   * @param id ノードID
   * @returns 成功したかどうか
   */
  async deleteNode(id: string): Promise<boolean> {
    try {
      return await this.graphDataService.deleteNode(id);
    } catch (error) {
      console.error(`Error deleting node ${id}:`, error);
      throw error;
    }
  }

  /**
   * ノードからフロントエンド表示用の階層構造データを生成する
   * @param fileNodes 元となるファイルノード配列
   * @returns 階層構造のルートノード
   */
  createNestedStructure(fileNodes: FileNodeType[]): FrontendNodeType {
    // ルートノード（仮想的な最上位ノード）
    const rootNode: FrontendNodeType = { id: 'root', name: 'root', path: '', children: [] };
    
    // 構造を構築するための一時的なマップ
    const pathMap = new Map<string, FrontendNodeType>();
    pathMap.set('', rootNode);
    
    console.log(`createNestedStructure: 入力ノード数=${fileNodes.length}`);
    // パスの形式を確認
    if (fileNodes.length > 0) {
      console.log("パスサンプル：", fileNodes[0].path);
      // :::があるかチェック
      const hasPathSeparator = fileNodes.some(node => node.path.includes(':::'));
      console.log(`パスセパレータ(:::)を含むノード: ${hasPathSeparator}`);
    }
    
    // ファイルパスをソート（親が先に処理されるように）
    const sortedNodes = [...fileNodes].sort((a, b) => {
      // パス部分のみを比較（関数名を除く）
      const aBase = a.path.split(':::')[0];
      const bBase = b.path.split(':::')[0];
      return aBase.localeCompare(bBase) || a.path.localeCompare(b.path);
    });
    
    // 作成されたディレクトリを追跡
    const createdDirs = new Set<string>();
    
    // 各ノードを処理して階層構造を構築
    sortedNodes.forEach(fileNode => {
      const { name, path } = fileNode;
      
      // パスを分解して階層を取得
      const parts = path.split(':::');
      const filePath = parts[0];
      const functionName = parts[1] || null;
      
      console.log(`処理中: パス=${path}, ファイルパス=${filePath}, 関数名=${functionName || 'なし'}`);
      
      // ファイルパスの部分を処理
      if (!functionName) {
        // ファイルパスのパーツに分解
        const pathParts = filePath.split('/');
        let currentPath = '';
        let parentPath = '';
        
        for (let i = 0; i < pathParts.length; i++) {
          parentPath = currentPath;
          currentPath = currentPath ? `${currentPath}/${pathParts[i]}` : pathParts[i];
          
          // 既に存在するパスならスキップ
          if (pathMap.has(currentPath)) {
            console.log(`スキップ: ${currentPath} (既存)`);
            continue;
          }
          
          console.log(`ディレクトリ作成: ${currentPath}`);
          createdDirs.add(currentPath);
          
          // 新しいノードを作成
          const node: FrontendNodeType = {
            id: currentPath,
            name: pathParts[i],
            path: currentPath,
            children: []
          };
          
          // 親ノードに追加
          const parentNode = pathMap.get(parentPath);
          if (parentNode && parentNode.children) {
            parentNode.children.push(node);
            console.log(`親ノード ${parentPath || 'root'} に ${currentPath} を追加`);
          } else {
            console.warn(`警告: 親ノード ${parentPath} が見つかりません`);
          }
          
          // マップに登録
          pathMap.set(currentPath, node);
        }
      } else {
        // 関数の場合、親ファイルに追加
        const parentNode = pathMap.get(filePath);
        
        if (parentNode && parentNode.children) {
          console.log(`関数追加: ${name} を ${filePath} に追加`);
          
          const node: FrontendNodeType = {
            id: path,
            name,
            path,
            children: []
          };
          parentNode.children.push(node);
          pathMap.set(path, node);
        } else {
          console.warn(`警告: 親ファイル ${filePath} が見つかりません。自動作成します。`);
          
          // 親ファイルが存在しない場合、自動的に作成
          // まずディレクトリ階層を作成
          const pathParts = filePath.split('/');
          let currentPath = '';
          let parentPath = '';
          
          for (let i = 0; i < pathParts.length; i++) {
            parentPath = currentPath;
            currentPath = currentPath ? `${currentPath}/${pathParts[i]}` : pathParts[i];
            
            if (!pathMap.has(currentPath)) {
              console.log(`自動ディレクトリ作成: ${currentPath}`);
              
              const dirNode: FrontendNodeType = {
                id: currentPath,
                name: pathParts[i],
                path: currentPath,
                children: []
              };
              
              const parentDirNode = pathMap.get(parentPath);
              if (parentDirNode && parentDirNode.children) {
                parentDirNode.children.push(dirNode);
              }
              
              pathMap.set(currentPath, dirNode);
            }
          }
          
          // 親ファイルが作成されたので改めて関数を追加
          const newParentNode = pathMap.get(filePath);
          if (newParentNode && newParentNode.children) {
            console.log(`関数追加(遅延): ${name} を ${filePath} に追加`);
            
            const node: FrontendNodeType = {
              id: path,
              name,
              path,
              children: []
            };
            newParentNode.children.push(node);
            pathMap.set(path, node);
          }
        }
      }
    });
    
    console.log(`階層構造作成完了: 作成ディレクトリ数=${createdDirs.size}`);
    console.log(`ルートノードの子の数: ${rootNode.children?.length || 0}`);
    
    if (rootNode.children && rootNode.children.length > 0) {
      console.log(`最初の子ノード: ${rootNode.children[0].name}, 子の数: ${rootNode.children[0].children?.length || 0}`);
      return rootNode.children[0];
    } else {
      console.warn("警告: ルートノードに子がないため 'No data' ノードを返します");
      return { id: 'empty', name: 'No data', path: '' };
    }
  }

  /**
   * ツリーの最大深度を計算
   * @param node ノード
   * @param currentDepth 現在の深さ
   * @returns 最大深度
   */
  calculateMaxDepth(node: FrontendNodeType, currentDepth = 0): number {
    if (!node.children || node.children.length === 0) {
      return currentDepth;
    }
    
    return Math.max(...node.children.map(child => 
      this.calculateMaxDepth(child, currentDepth + 1)
    ));
  }
}

export default NodeRepository;