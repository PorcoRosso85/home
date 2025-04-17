// platform/browser/pathUtils.ts - ブラウザ向けのパス操作ユーティリティ実装

import { PathUtils } from '../../core/types.ts';

/**
 * ブラウザ用のシンプルなパスユーティリティ実装
 */
export const browserPathUtils: PathUtils = {
  /**
   * パスの要素を結合する
   */
  join(...paths: string[]): string {
    // 空のパス要素を除外
    const parts = paths.filter(part => part);
    
    if (parts.length === 0) return '';
    
    // 絶対パスかどうかを判断
    const isAbsolute = parts[0].startsWith('/');
    
    // パスを正規化して結合
    const normalizedParts: string[] = [];
    
    for (const part of parts) {
      // 各パーツを / で分割
      const segments = part.split('/').filter(segment => segment && segment !== '.');
      
      for (const segment of segments) {
        if (segment === '..') {
          // 親ディレクトリに移動
          normalizedParts.pop();
        } else {
          normalizedParts.push(segment);
        }
      }
    }
    
    // 最終的なパスを構築
    let result = normalizedParts.join('/');
    if (isAbsolute) {
      result = '/' + result;
    }
    
    return result || (isAbsolute ? '/' : '.');
  },
  
  /**
   * パスの親ディレクトリを取得
   */
  dirname(path: string): string {
    if (!path) return '.';
    
    // 末尾のスラッシュを削除
    path = path.endsWith('/') ? path.slice(0, -1) : path;
    
    const lastSlashIndex = path.lastIndexOf('/');
    if (lastSlashIndex === -1) return '.';
    
    // ルートディレクトリの場合
    if (lastSlashIndex === 0) return '/';
    
    return path.slice(0, lastSlashIndex);
  },
  
  /**
   * fromパスからtoパスへの相対パスを取得
   */
  relative(from: string, to: string): string {
    if (from === to) return '';
    
    // 絶対パスに変換
    from = this.join('/', from);
    to = this.join('/', to);
    
    // 共通のプレフィックスを見つける
    const fromParts = from.split('/').filter(Boolean);
    const toParts = to.split('/').filter(Boolean);
    
    let commonPrefixLength = 0;
    const minLength = Math.min(fromParts.length, toParts.length);
    
    while (commonPrefixLength < minLength && 
           fromParts[commonPrefixLength] === toParts[commonPrefixLength]) {
      commonPrefixLength++;
    }
    
    // 上位ディレクトリへの移動
    const upCount = fromParts.length - commonPrefixLength;
    const upSegments = new Array(upCount).fill('..');
    
    // 残りのセグメントを追加
    const downSegments = toParts.slice(commonPrefixLength);
    
    const result = [...upSegments, ...downSegments].join('/');
    return result || '.';
  },
  
  /**
   * ファイルの拡張子を取得
   */
  extname(path: string): string {
    const lastDotIndex = path.lastIndexOf('.');
    const lastSlashIndex = path.lastIndexOf('/');
    
    // ドットがない場合、または最後のスラッシュの前にドットがある場合（隠しファイル）
    if (lastDotIndex < 0 || (lastSlashIndex > -1 && lastDotIndex < lastSlashIndex)) {
      return '';
    }
    
    return path.slice(lastDotIndex);
  },
  
  /**
   * ファイル名を取得
   */
  basename(path: string): string {
    // 末尾のスラッシュを削除
    path = path.endsWith('/') ? path.slice(0, -1) : path;
    
    const lastSlashIndex = path.lastIndexOf('/');
    if (lastSlashIndex === -1) return path;
    
    return path.slice(lastSlashIndex + 1);
  }
};
