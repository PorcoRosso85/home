import Lean
import Src.Refer
open Lean Meta Elab Command

class Collection (c : Type) where
  ElemType : Type
  insert : c → ElemType → c

inductive RegisterError where
  | UsernameTaken (message : String)
  | InvalidUsername (message : String) -- 例：無効なユーザー名エラー
  | DatabaseError (message : String)   -- 例：データベースエラー

inductive User where
  | ok (id : Nat) (name : String)

class UserRegistrar (m : Type → Type) where
  registerUser : String → m (Except RegisterError User)

instance : ToString RegisterError where
  toString err := match err with
    | RegisterError.UsernameTaken name => s!"Username '{name}' is already taken."
    | RegisterError.InvalidUsername reason => s!"Invalid username: {reason}"
    | RegisterError.DatabaseError reason => s!"Database error: {reason}"

-- IOモナドを使ったUserRegistrarのインスタンス
instance : UserRegistrar IO where
  registerUser name := do
    -- 副作用の例：ログ出力
    IO.println s!"Registering user: {name}"
    -- エラーの例：ユーザー名が "Bob" の場合は登録失敗
    if name == "Bob" then
      return Except.error (RegisterError.UsernameTaken name)
    -- 副作用の例：データベースへの書き込み (ここでは省略)
    -- ... データベース書き込み処理 ...
    else
      pure $ Except.ok $ User.ok 123 name -- ダミーのUserIdとUserオブジェクトを返す

def main : IO Unit := do
  let registrar : UserRegistrar IO := inferInstance -- IO モナドのインスタンスを取得
  let result := registrar.registerUser "Alice" -- ユーザー登録処理を実行
  match (← result) with  -- パターンマッチングを開始
    | Except.ok user => match user with
      | User.ok id name =>
        IO.println s!"Registered user: {name}, id: {id}"
    | Except.error err => -- 登録失敗
      IO.println s!"Registration failed: {ToString.toString err}"

#eval main

-- 単一の型に対してテスト
#eval show MetaM Unit from do
  let deps ← getInductiveTypeDeps `User
  IO.println s!"{deps}"
  let deps ← getInductiveTypeDeps `RegisterError
  IO.println s!"{deps}"
  let deps ← getInductiveTypeDeps `UserRegister
  IO.println s!"{deps}"
