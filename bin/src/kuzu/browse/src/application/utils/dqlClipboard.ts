/**
 * DQLクリップボード機能の単一責務関数群
 */

/**
 * DQLファイルの内容を読み込む
 */
export async function readDQLFile(queryName: string): Promise<string> {
  try {
    const response = await fetch(`/dql/${queryName}.cypher`);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${queryName}.cypher: ${response.status} ${response.statusText}`);
    }
    const content = await response.text();
    return content;
  } catch (error) {
    console.error('DQLファイル読み込みエラー:', error);
    return `// ${queryName}.cypher の読み込みに失敗しました\n// エラー: ${error.message}`;
  }
}

/**
 * パラメータをDQLクエリに埋め込む
 */
export function embedParameters(dqlContent: string, params: Record<string, string>): string {
  let result = dqlContent;
  Object.entries(params).forEach(([key, value]) => {
    result = result.replace(new RegExp(`\\$${key}`, 'g'), `"${value}"`);
  });
  return result;
}

/**
 * テキストをクリップボードにコピーする
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('クリップボードコピーエラー:', error);
    return false;
  }
}
/**
 * DQLクエリをクリップボードにコピーする統合関数
 */
export async function copyDQLToClipboard(
  queryName: string, 
  params: Record<string, string> = {}
): Promise<boolean> {
  const dqlContent = await readDQLFile(queryName);
  const finalQuery = embedParameters(dqlContent, params);
  return await copyToClipboard(finalQuery);
}
