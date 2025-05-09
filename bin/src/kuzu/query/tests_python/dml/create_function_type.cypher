// 関数型ノードを作成する
CREATE (f:FunctionType {
  title: $title,
  description: $description,
  type: $type,
  pure: $pure,
  async: $async
})