/**
 * シンプルプロンプト生成器
 * CONVENTION.yaml規約準拠: 最小構成、関数のみ
 */

import type { NodeData } from '../../domain/types.ts';
import * as logger from '../../../common/infrastructure/logger.ts';

/**
 * バージョン解析用の固定プロンプト生成
 */
function generateVersionAnalysisPrompt(node: NodeData): string {
  const basePrompt = "このバージョンで変更されるuriはどれ？";
  
  // ノードデータを文脈として追加
  const context = `
バージョン情報:
- ID: ${node.id}
- 名前: ${node.name}
- 説明: ${node.description || 'なし'}
- 変更理由: ${node.change_reason || 'なし'}
- タイムスタンプ: ${node.timestamp || 'なし'}

${basePrompt}

上記のバージョン情報を基に、変更されるURIについて分析してください。
`;

  const finalPrompt = context.trim();
  
  // DevTools にリクエスト内容をログ出力
  logger.info('Claude解析リクエスト生成', {
    versionId: node.id,
    versionName: node.name,
    prompt: basePrompt,
    contextLength: finalPrompt.length
  });

  return finalPrompt;
}

/**
 * エラー時のフォールバックプロンプト
 */
function generateFallbackPrompt(): string {
  return `バージョン情報の取得に失敗しました。
一般的なバージョン管理における変更点について説明してください。`;
}

export { 
  generateVersionAnalysisPrompt, 
  generateFallbackPrompt 
};
