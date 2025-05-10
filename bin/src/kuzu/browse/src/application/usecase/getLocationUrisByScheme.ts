import type { LocationUri } from '../../domain/entity/locationUri';
import * as logger from '../../../../common/infrastructure/logger';
import { getLocationUris } from './getLocationUris';

export async function getLocationUrisByScheme(scheme: string): Promise<LocationUri[]> {
  const allUris = await getLocationUris();
  const filtered = allUris.filter(uri => uri.scheme === scheme);
  logger.info(`フィルタリング結果: ${filtered.length}件（scheme=${scheme}）`);
  return filtered;
}
