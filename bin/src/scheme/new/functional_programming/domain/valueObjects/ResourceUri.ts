/**
 * ResourceUri.ts
 * 
 * 関数実装のリソースURIを表現する値オブジェクト
 */

/**
 * リソースURIの種類を表す列挙型
 */
export enum ResourceUriType {
  FILE = 'file',
  HTTP = 'http',
  HTTPS = 'https',
  GIT = 'git',
  UNKNOWN = 'unknown'
}

/**
 * リソースURIを表す値オブジェクト
 * 異なる環境間での互換性を保つため、URIフォーマットに統一する
 */
export class ResourceUri {
  private readonly _value: string;
  private readonly _type: ResourceUriType;

  /**
   * コンストラクタ
   * @param value URI文字列
   */
  private constructor(value: string, type: ResourceUriType) {
    this._value = value;
    this._type = type;
  }

  /**
   * 値を取得
   */
  get value(): string {
    return this._value;
  }

  /**
   * 種類を取得
   */
  get type(): ResourceUriType {
    return this._type;
  }

  /**
   * 値オブジェクトの等価性比較
   * @param other 比較対象
   * @returns 等価の場合true
   */
  equals(other: ResourceUri): boolean {
    if (!(other instanceof ResourceUri)) {
      return false;
    }
    return this._value === other._value;
  }

  /**
   * 文字列に変換
   * @returns URI文字列
   */
  toString(): string {
    return this._value;
  }

  /**
   * JSONシリアライズ時の挙動を定義
   * @returns 文字列表現
   */
  toJSON(): string {
    return this._value;
  }

  /**
   * URIの種類を判定
   * @param uri URI文字列
   * @returns URIの種類
   */
  private static determineType(uri: string): ResourceUriType {
    if (uri.startsWith('file:')) return ResourceUriType.FILE;
    if (uri.startsWith('http:')) return ResourceUriType.HTTP;
    if (uri.startsWith('https:')) return ResourceUriType.HTTPS;
    if (uri.startsWith('git:')) return ResourceUriType.GIT;
    return ResourceUriType.UNKNOWN;
  }

  /**
   * ファクトリメソッド - 生のURI文字列から作成
   * @param uri URI文字列
   * @returns ResourceUriインスタンス
   * @throws Error 無効なURIの場合
   */
  static create(uri: string): ResourceUri {
    if (!uri) {
      throw new Error('リソースURIは空であってはなりません');
    }

    // 既にURI形式の場合はそのまま使用
    if (uri.includes('://')) {
      const type = this.determineType(uri);
      return new ResourceUri(uri, type);
    }

    // 絶対パスをfile URLに変換
    if (uri.startsWith('/')) {
      return new ResourceUri(`file://${uri}`, ResourceUriType.FILE);
    }

    // 相対パスは許可しない（ポリシーに基づく）
    if (uri.startsWith('./') || uri.startsWith('../')) {
      throw new Error('相対パスはサポートされていません。絶対パスまたはURI形式を使用してください。');
    }

    // その他の形式はそのままfile URLとして扱う
    return new ResourceUri(`file://${uri}`, ResourceUriType.FILE);
  }

  /**
   * 絶対パスからfile URLを作成
   * @param path 絶対パス
   * @returns ResourceUriインスタンス
   * @throws Error 絶対パスでない場合
   */
  static fromAbsolutePath(path: string): ResourceUri {
    if (!path.startsWith('/')) {
      throw new Error('絶対パスである必要があります');
    }
    return new ResourceUri(`file://${path}`, ResourceUriType.FILE);
  }

  /**
   * file URLをパスに変換
   * @returns ファイルシステムパス（file://プレフィックスを除去）
   * @throws Error file URLでない場合
   */
  toFilePath(): string {
    if (this._type !== ResourceUriType.FILE) {
      throw new Error('このURIはファイルURIではありません');
    }
    // file:// または file:/// プレフィックスを除去
    return this._value.replace(/^file:\/\/\//, '/').replace(/^file:\/\//, '/');
  }
}
