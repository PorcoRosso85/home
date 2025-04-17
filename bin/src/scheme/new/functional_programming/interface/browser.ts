/**
 * browser.ts
 * 
 * ブラウザ用のメインエントリポイント
 * DOM操作を伴うブラウザ固有の実装
 * 
 * 使用方法:
 * ```html
 * <script type="module">
 *   import { initializeApp } from './browser.js';
 *   
 *   document.addEventListener('DOMContentLoaded', () => {
 *     initializeApp();
 *   });
 * </script>
 * ```
 * 
 * コンパイル方法:
 * ```bash
 * # nixpkgsを使用してDenoでコンパイルする
 * nix-shell -p deno --run "deno bundle browser.ts dist/browser.js"
 * ```
 */

// ブラウザアプリケーションのエントリーポイントを再エクスポート
export { initializeApp } from './browser/index.ts';
