// Example: Using Shiki with WASM for syntax highlighting
import { getHighlighter, type Highlighter } from 'shiki';

let highlighterInstance: Highlighter | null = null;

/**
 * Initialize Shiki highlighter with WASM
 * The WASM files from Shiki will be automatically handled by @cloudflare/vite-plugin
 */
export async function initHighlighter(): Promise<Highlighter> {
  if (!highlighterInstance) {
    highlighterInstance = await getHighlighter({
      themes: ['github-dark', 'github-light'],
      langs: ['javascript', 'typescript', 'jsx', 'tsx', 'json', 'markdown']
    });
  }
  return highlighterInstance;
}

/**
 * Highlight code using Shiki
 */
export async function highlightCode(
  code: string,
  lang: string = 'javascript',
  theme: 'github-dark' | 'github-light' = 'github-dark'
): Promise<string> {
  const highlighter = await initHighlighter();
  return highlighter.codeToHtml(code, { lang, theme });
}

/**
 * Example of direct WASM import (if you have a custom .wasm file)
 * Uncomment and replace with your actual WASM file
 */
// import customWasm from './custom.wasm';
// 
// export async function useCustomWasm() {
//   const instance = await WebAssembly.instantiate(customWasm);
//   return instance.exports;
// }