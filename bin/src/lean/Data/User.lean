import Lean

inductive User where
  | mk : String -> Nat -> User -- コンストラクタ: mk (名前, 年齢)

inductive Result (α : Type) where
  | ok : α -> Result α       -- コンストラクタ: ok (成功時の値)
  | error : String -> Result α  -- コンストラクタ: error (エラーメッセージ)

-- 1. UserRequest 型 (ユーザー作成要求)
inductive UserRequest where
  | create : String -> Nat -> UserRequest -- コンストラクタ: create (名前, 年齢)
  -- ユーザー作成を要求する際に必要な情報 (名前と年齢) を保持

-- 2. UserCreationResponse 型 (ユーザー作成処理応答)
inductive UserCreationResponse where
  | success : User -> UserCreationResponse         -- コンストラクタ: success (作成されたユーザー情報)
  | failure : String -> UserCreationResponse         -- コンストラクタ: failure (失敗理由)
  -- ユーザー作成処理の最終的な応答を表す。
  -- success コンストラクタは作成成功、failure コンストラクタは作成失敗を表す

#check UserCreationResponse.success




#eval "UserCreationResponse.successが？"
