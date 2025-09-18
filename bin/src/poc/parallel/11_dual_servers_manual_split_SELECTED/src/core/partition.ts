// 純粋なビジネスロジック
// bin/docs規約準拠: 純粋関数を優先、副作用なし

/**
 * ユーザーIDが指定されたパーティションに属するかを判定する純粋関数
 */
export function isInPartition(userId: string, partitionKey: string): boolean {
  const firstChar = userId[0].toUpperCase();
  
  if (partitionKey === 'A-M') {
    return firstChar >= 'A' && firstChar <= 'M';
  } else if (partitionKey === 'N-Z') {
    return firstChar >= 'N' && firstChar <= 'Z';
  }
  
  return false;
}

/**
 * ユーザーIDから正しいサーバー名を取得する純粋関数
 */
export function getCorrectServer(
  userId: string, 
  currentServer: string, 
  currentPartition: string,
  peerServer: string
): string {
  return isInPartition(userId, currentPartition) ? currentServer : peerServer;
}

/**
 * パーティションキーの妥当性を検証する純粋関数
 */
export function isValidPartitionKey(partitionKey: string): boolean {
  return partitionKey === 'A-M' || partitionKey === 'N-Z';
}

/**
 * 2つのパーティションキーが相補的かを検証する純粋関数
 */
export function areComplementaryPartitions(key1: string, key2: string): boolean {
  return (key1 === 'A-M' && key2 === 'N-Z') || 
         (key1 === 'N-Z' && key2 === 'A-M');
}