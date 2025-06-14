import Lean.Elab.Command
import Lean.Elab.Term
import Lean.Meta
import Lean.Elab.Frontend
-- import Src.Basic -- 今回はSrc.Basicは不要

open Lean
open Lean.Meta
open Lean.Elab.Command

/-- 型名と型定義を受け取り、型定義コマンドを生成・評価する汎用関数 -/
def generateGenericType (typeName : Name) (typeDef : TSyntax `term) : CommandElabM Unit := do
  -- 型定義コマンドを準クォートで作成
  let cmdQuoted := `(command| def $(mkIdent typeName) := $typeDef)
  let cmd ← cmdQuoted
  -- コマンドを評価して型定義を実行
  elabCommand cmd.raw

/-- Unit型生成の共通関数 (汎用型生成関数を使用) -/
def generateUnitType (typeName : Name) (typeTermName : Name) : CommandElabM Unit := do
  -- 型定義の元となる型の構文オブジェクトを取得
  let typeTermSyntax ← `(term| $(mkIdent typeTermName))
  -- 汎用型生成関数を呼び出して型を生成
  generateGenericType typeName typeTermSyntax

/-- UserId型を生成する (共通unit生成関数を使用) -/
def generateUserIdType : CommandElabM Unit := do
  generateUnitType `UserId `Nat

/-- User型を生成する (構造体として直接定義) -/
def generateUserType : CommandElabM Unit := do
  -- User構造体の定義を準クォートで作成
  let cmd ← `(command|
    structure User where
      id : UserId
      name : String
      email : String
      active : Bool
    deriving Repr)
  -- 構造体定義コマンドを直接実行
  elabCommand cmd.raw

def main : IO Unit := do
  -- UserId型とUser型を生成
  Lean.Elab.Frontend.runFrontend do
  -- Lean.runElab do
  -- Elab.Command.liftMacroM do
  -- Command.liftMacroM do
  -- runCommandElabM do
    generateUserIdType
    -- generateUserType -- User型生成は一旦コメントアウト

    -- UserId型が正しく生成されているか確認するためのテストコード
    -- UserId は Nat の別名として定義されているので、Nat の値をそのまま使える
    let userIdValue : UserId := 123
    IO.println "UserId value:"
    IO.println userIdValue -- Repr がないので、そのままでは Nat として表示される

    -- UserId の型名を確認 (MetaM 内で実行する必要がある)
    runMetaM {} do
      let userIdIdent := mkIdent `UserId
      let userIdType ← elabType userIdIdent
      IO.println "UserId type name:"
      IO.println userIdType

    -- User型が正しく生成されているか確認するためのテストコード (一旦コメントアウト)
    -- let userValue := User.mk userIdValue "John Doe" "john.doe@example.com" true
    -- IO.println "User value:"
    -- IO.println (repr userValue)
