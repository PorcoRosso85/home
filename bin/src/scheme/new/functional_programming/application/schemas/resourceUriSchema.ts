/**
 * resourceUriSchema.ts
 * 
 * リソースURIのスキーマを生成する関数
 */

/**
 * リソースURIのスキーマを生成
 * 
 * @returns リソースURIスキーマ
 */
export function createResourceUriSchema(): any {
  return {
    type: 'string',
    description: '関数の実装リソースへの参照URI',
    examples: [
      'file:///src/utils/math.ts',
      'https://github.com/user/repo/blob/main/src/utils/math.ts',
      'git://github.com/user/repo.git#path=src/utils/math.ts',
      '/absolute/path/to/file.ts',
      './relative/path/to/file.ts'
    ]
  };
}
