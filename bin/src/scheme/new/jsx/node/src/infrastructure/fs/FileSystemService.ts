/**
 * FileSystem Access APIを使用してローカルファイルシステムにアクセスするサービス
 * Web標準のFileSystem Access APIを使用して、ブラウザから直接ファイルの読み書きを行う
 * 
 * TODO: WSL環境からWindowsのブラウザを使用する場合、ファイルシステムパスの扱いに問題が
 * 発生することがあります。WSL固有の問題として、FileSystem Access APIの利用が制限される
 * 可能性があるため、代替手段としてLocalStorageベースの実装に切り替えています。
 * 将来的にはネイティブ環境で動作させる場合、この実装を活用できる可能性があります。
 */
export interface FileHandleWithPath {
  handle: FileSystemFileHandle;
  path: string;
}

export interface DirectoryHandleWithPath {
  handle: FileSystemDirectoryHandle;
  path: string;
}

class FileSystemService {
  // 開いているファイルハンドルを格納
  private fileHandles: Map<string, FileSystemFileHandle> = new Map();
  // 開いているディレクトリハンドルを格納
  private directoryHandle: FileSystemDirectoryHandle | null = null;
  // 現在のプロジェクトディレクトリパス
  private _currentDirectory: string = '';

  /**
   * クラスが初期化されたときにFileSystem Access APIが利用可能かチェック
   */
  constructor() {
    if (!this.isFileSystemAccessSupported()) {
      console.warn('FileSystem Access API is not supported in this browser.');
    }
  }

  /**
   * 現在のディレクトリパスを取得
   */
  get currentDirectory(): string {
    return this._currentDirectory;
  }

  /**
   * FileSystem Access APIがサポートされているかチェック
   */
  isFileSystemAccessSupported(): boolean {
    return 'showOpenFilePicker' in window && 'showDirectoryPicker' in window;
  }

  /**
   * ディレクトリ選択ダイアログを表示し、選択されたディレクトリへのアクセス権を取得
   */
  async selectDirectory(): Promise<DirectoryHandleWithPath | null> {
    try {
      // ユーザーにディレクトリを選択してもらう
      const handle = await window.showDirectoryPicker({
        id: 'graph-db-directory',
        mode: 'readwrite',
        startIn: 'documents',
      });

      const path = handle.name;
      this.directoryHandle = handle;
      this._currentDirectory = path;

      return { handle, path };
    } catch (error) {
      // ユーザーがキャンセルした場合やエラーが発生した場合
      console.error('Error selecting directory:', error);
      return null;
    }
  }

  /**
   * 指定された名前のファイルを現在のディレクトリから読み込む
   */
  async readFile(fileName: string): Promise<string | null> {
    if (!this.directoryHandle) {
      throw new Error('No directory is selected. Please select a directory first.');
    }

    try {
      // ディレクトリから指定されたファイルを取得
      const fileHandle = await this.directoryHandle.getFileHandle(fileName);
      // ファイルハンドルをキャッシュ
      this.fileHandles.set(fileName, fileHandle);
      
      // ファイルの内容を読み込む
      const file = await fileHandle.getFile();
      return await file.text();
    } catch (error) {
      console.error(`Error reading file ${fileName}:`, error);
      
      // ENOENT相当のエラー（ファイルが存在しない）
      if ((error as any).name === 'NotFoundError') {
        return null;
      }
      
      throw error;
    }
  }

  /**
   * 指定された名前でファイルを現在のディレクトリに書き込む
   */
  async writeFile(fileName: string, content: string): Promise<boolean> {
    if (!this.directoryHandle) {
      throw new Error('No directory is selected. Please select a directory first.');
    }

    try {
      // ファイルが既にキャッシュされているか、新規作成か
      let fileHandle: FileSystemFileHandle;
      
      if (this.fileHandles.has(fileName)) {
        fileHandle = this.fileHandles.get(fileName)!;
      } else {
        // ファイルが存在すればそれを取得し、なければ新規作成
        fileHandle = await this.directoryHandle.getFileHandle(fileName, { create: true });
        this.fileHandles.set(fileName, fileHandle);
      }

      // 書き込み用のストリームを取得
      const writable = await fileHandle.createWritable();
      
      // ファイルにデータを書き込む
      await writable.write(content);
      
      // ストリームを閉じて書き込みを確定
      await writable.close();
      
      return true;
    } catch (error) {
      console.error(`Error writing file ${fileName}:`, error);
      return false;
    }
  }

  /**
   * ファイル選択ダイアログを表示し、選択されたJSONファイルをインポート
   */
  async importJsonFile(): Promise<{ name: string; content: string } | null> {
    try {
      // ユーザーにJSONファイルを選択してもらう
      const [fileHandle] = await window.showOpenFilePicker({
        types: [{
          description: 'JSON Files',
          accept: {
            'application/json': ['.json'],
          },
        }],
        multiple: false,
      });
      
      // ファイルの内容を読み込む
      const file = await fileHandle.getFile();
      const content = await file.text();
      
      return {
        name: file.name,
        content,
      };
    } catch (error) {
      console.error('Error importing JSON file:', error);
      return null;
    }
  }

  /**
   * 指定された内容でファイルを保存するダイアログを表示
   */
  async exportJsonFile(fileName: string, content: string): Promise<boolean> {
    try {
      // ユーザーにファイルの保存場所を選択してもらう
      const fileHandle = await window.showSaveFilePicker({
        suggestedName: fileName,
        types: [{
          description: 'JSON Files',
          accept: {
            'application/json': ['.json'],
          },
        }],
      });
      
      // 書き込み用のストリームを取得
      const writable = await fileHandle.createWritable();
      
      // ファイルにデータを書き込む
      await writable.write(content);
      
      // ストリームを閉じて書き込みを確定
      await writable.close();
      
      return true;
    } catch (error) {
      console.error(`Error exporting file ${fileName}:`, error);
      return false;
    }
  }

  /**
   * 現在のディレクトリ内のJSONファイル一覧を取得
   */
  async listJsonFiles(): Promise<string[]> {
    if (!this.directoryHandle) {
      throw new Error('No directory is selected. Please select a directory first.');
    }

    const jsonFiles: string[] = [];
    
    try {
      // ディレクトリ内の全ファイルをイテレート
      for await (const [name, handle] of this.directoryHandle.entries()) {
        // ファイルのみを対象とし、.jsonで終わるものを抽出
        if (handle.kind === 'file' && name.endsWith('.json')) {
          jsonFiles.push(name);
        }
      }
      
      return jsonFiles;
    } catch (error) {
      console.error('Error listing JSON files:', error);
      throw error;
    }
  }

  /**
   * 永続的なアクセス権限を要求
   */
  async requestPersistentAccess(): Promise<boolean> {
    if (!this.directoryHandle) {
      return false;
    }

    try {
      // 'readwrite'権限を要求
      const permission = await this.directoryHandle.requestPermission({ mode: 'readwrite' });
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting persistent access:', error);
      return false;
    }
  }

  /**
   * ファイルが存在するかチェック
   */
  async fileExists(fileName: string): Promise<boolean> {
    if (!this.directoryHandle) {
      throw new Error('No directory is selected. Please select a directory first.');
    }

    try {
      await this.directoryHandle.getFileHandle(fileName);
      return true;
    } catch (error) {
      if ((error as any).name === 'NotFoundError') {
        return false;
      }
      throw error;
    }
  }
}

export default FileSystemService;
