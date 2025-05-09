// パラメータノードを作成する
CREATE (p:Parameter {
  name: $name,
  type: $type,
  description: $description,
  required: $required
})