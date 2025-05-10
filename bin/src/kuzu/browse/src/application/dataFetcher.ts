import type { LocationUri } from '../../../query/domain/uriTypes';
import type { TreeNodeData } from '../interface/components/TreeNode';
import { buildDynamicTree } from './uriParser';

/**
 * KuzuDBからLocationUri一覧を取得
 */
export async function fetchLocationUris(): Promise<LocationUri[]> {
  try {
    // TODO: 実際のKuzuDBから取得する処理を実装
    // 現在はダミーデータを返す
    const dummyLocationUris: LocationUri[] = [
      {
        uri_id: 'file:///src/main.ts',
        scheme: 'file',
        authority: '',
        path: '/src/main.ts',
        fragment: '',
        query: ''
      },
      {
        uri_id: 'file:///src/utils.ts',
        scheme: 'file',
        authority: '',
        path: '/src/utils.ts',
        fragment: '',
        query: ''
      },
      {
        uri_id: 'file:///src/components/app.tsx',
        scheme: 'file',
        authority: '',
        path: '/src/components/app.tsx',
        fragment: '',
        query: ''
      },
      // 既存のダミーデータ互換形式
      {
        uri_id: '/nodes/person/1',
        scheme: 'path',
        authority: '',
        path: '/nodes/person/1',
        fragment: '',
        query: ''
      },
      {
        uri_id: '/nodes/person/1/knows/person/2',
        scheme: 'path',
        authority: '',
        path: '/nodes/person/1/knows/person/2',
        fragment: '',
        query: ''
      },
      {
        uri_id: '/nodes/person/1/lives_in/city/3',
        scheme: 'path',
        authority: '',
        path: '/nodes/person/1/lives_in/city/3',
        fragment: '',
        query: ''
      }
    ];
    
    return dummyLocationUris;
  } catch (error) {
    console.error('Failed to fetch LocationUris:', error);
    return [];
  }
}

/**
 * LocationUriからツリーデータを構築
 */
export async function fetchAndBuildTree(): Promise<TreeNodeData[]> {
  const locationUris = await fetchLocationUris();
  return buildDynamicTree(locationUris);
}

/**
 * 特定のスキームのLocationUriを取得
 */
export async function fetchLocationUrisByScheme(scheme: string): Promise<LocationUri[]> {
  const allUris = await fetchLocationUris();
  return allUris.filter(uri => uri.scheme === scheme);
}
