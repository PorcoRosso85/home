import Lean

/-
json schema例
スキーマが満たすキーとそのキーがあることで満たされるべき要件
- definedByLean: leanファイルのコード、これをプロンプトとして使用することでleanで証明された要件が実際の実装コードで満たされることを保証する
- description: 'definedByLean'に属性追加されているドキュメント値
- definitionAddress: leanファイルとシンボルのパス
- symbolAddress: この定義が実装として計画されるパス、プロジェクトルートからの相対パス+'#シンボル名'で表現される 'eg ./path/to/file.ext#symbol'
-/
def main : IO Unit := do
  IO.println s!"hi"

-- TODO
-- - leanの型定義のコードそのものを文字列として返却する
#eval main
