// 戻り値型ノードを作成する
CREATE (r:ReturnType {
  type: $type,
  description: $description
})