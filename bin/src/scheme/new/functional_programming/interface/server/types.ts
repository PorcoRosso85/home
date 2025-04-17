/**
 * インターフェース層で使用する型定義
 */

/**
 * 関数データ型
 */
export interface FunctionData {
  /** 関数のパス（file/to/path.xxx:::func_name形式） */
  path: string;
  /** 関数のメタデータ */
  metadata: {
    /** 関数の説明 */
    description?: string;
    /** 戻り値の型 */
    returnType?: string;
    /** パラメータリスト */
    parameters?: string[];
    /** その他のメタデータ */
    [key: string]: unknown;
  };
}

/**
 * APIレスポンスの共通型
 */
export interface ApiResponse<T> {
  /** データ本体 */
  data?: T;
  /** エラーメッセージ（エラー時のみ） */
  error?: string;
  /** ステータスコード */
  status: number;
}
