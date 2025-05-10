import type { TreeNodeData } from '../../domain/entity/locationUri';
import * as logger from '../../../../common/infrastructure/logger';
import { getLocationUris } from './getLocationUris';
import { buildTree } from '../../domain/service/locationTreeBuilder';

export async function buildLocationTree(): Promise<TreeNodeData[]> {
  logger.debug('ツリーデータ構築開始');
  const locationUris = await getLocationUris();
  const tree = buildTree(locationUris);
  logger.debug(`ツリーデータ構築完了: ${tree.length}ノード`);
  return tree;
}
