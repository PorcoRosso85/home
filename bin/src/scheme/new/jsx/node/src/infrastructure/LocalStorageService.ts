/**
 * LocalStorageを使ってグラフデータを管理するサービス
 * JSON形式のデータをブラウザのLocalStorageに保存・読込する
 */
class LocalStorageService {
  private readonly PREFIX = 'graph_data_';
  
  /**
   * 指定されたキーでデータをLocalStorageから読み込む
   * @param key キー名
   * @returns JSONでパースしたデータ、存在しない場合はnull
   */
  loadData<T>(key: string): T | null {
    try {
      const data = localStorage.getItem(this.PREFIX + key);
      if (!data) {
        return null;
      }
      return JSON.parse(data) as T;
    } catch (error) {
      console.error(`Error loading data from localStorage (${key}):`, error);
      return null;
    }
  }
  
  /**
   * 指定されたキーでデータをLocalStorageに保存
   * @param key キー名
   * @param data 保存するデータ
   * @returns 成功したかどうか
   */
  saveData<T>(key: string, data: T): boolean {
    try {
      const jsonData = JSON.stringify(data);
      localStorage.setItem(this.PREFIX + key, jsonData);
      return true;
    } catch (error) {
      console.error(`Error saving data to localStorage (${key}):`, error);
      return false;
    }
  }
  
  /**
   * 指定されたキーのデータをLocalStorageから削除
   * @param key キー名
   * @returns 成功したかどうか
   */
  removeData(key: string): boolean {
    try {
      localStorage.removeItem(this.PREFIX + key);
      return true;
    } catch (error) {
      console.error(`Error removing data from localStorage (${key}):`, error);
      return false;
    }
  }
  
  /**
   * すべてのグラフデータをLocalStorageから削除
   * @returns 成功したかどうか
   */
  clearAllData(): boolean {
    try {
      // プレフィックスが一致するキーのみ削除
      Object.keys(localStorage)
        .filter(key => key.startsWith(this.PREFIX))
        .forEach(key => localStorage.removeItem(key));
      return true;
    } catch (error) {
      console.error('Error clearing all data from localStorage:', error);
      return false;
    }
  }
  
  /**
   * LocalStorageの使用状況を取得
   * @returns 使用量情報
   */
  getStorageInfo(): { used: number; total: number; percentage: number } {
    const total = 5 * 1024 * 1024; // 一般的なブラウザのLocalStorage上限は5MB
    let used = 0;
    
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          const value = localStorage.getItem(key) || '';
          used += key.length + value.length;
        }
      }
      
      // 2バイト文字を考慮して2倍
      used = used * 2;
      
      return {
        used,
        total,
        percentage: (used / total) * 100
      };
    } catch (error) {
      console.error('Error getting storage info:', error);
      return { used: 0, total, percentage: 0 };
    }
  }
  
  /**
   * JSON文字列をBlobとしてダウンロード
   * @param fileName ファイル名
   * @param jsonData JSONデータ
   */
  downloadJson(fileName: string, jsonData: any): void {
    try {
      // オブジェクトをJSON文字列に変換
      const jsonString = JSON.stringify(jsonData, null, 2);
      
      // Blobを作成
      const blob = new Blob([jsonString], { type: 'application/json' });
      
      // ダウンロードリンクを作成
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      
      // リンクをクリックしてダウンロードを開始
      document.body.appendChild(a);
      a.click();
      
      // 不要になったら要素とURLを削除
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
    } catch (error) {
      console.error(`Error downloading JSON (${fileName}):`, error);
    }
  }
  
  /**
   * ファイル選択ダイアログからJSONファイルを読み込む
   * @returns Promise<{ name: string; content: any }> ファイル名とJSONデータ
   */
  loadJsonFromFile(): Promise<{ name: string; content: any } | null> {
    return new Promise((resolve) => {
      try {
        // ファイル入力要素を作成
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'application/json';
        
        // ファイル選択時の処理
        input.onchange = (event) => {
          const target = event.target as HTMLInputElement;
          const files = target.files;
          
          if (files && files.length > 0) {
            const file = files[0];
            const reader = new FileReader();
            
            reader.onload = (e) => {
              try {
                const content = JSON.parse(e.target?.result as string);
                resolve({ name: file.name, content });
              } catch (error) {
                console.error('Error parsing JSON file:', error);
                resolve(null);
              }
            };
            
            reader.onerror = () => {
              console.error('Error reading file');
              resolve(null);
            };
            
            reader.readAsText(file);
          } else {
            resolve(null);
          }
        };
        
        // キャンセル時の処理
        input.onabort = () => resolve(null);
        
        // ファイル選択ダイアログを表示
        input.click();
      } catch (error) {
        console.error('Error loading JSON from file:', error);
        resolve(null);
      }
    });
  }
}

export default LocalStorageService;