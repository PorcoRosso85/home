-- ユーザーデータを表現する型
structure User where
  id : Nat
  username : String
  email : String
  passwordHash : String
  deriving Repr

-- 登録処理で発生しうるエラーを表現する型
inductive RegistrationError where
  | UsernameExists
  | InvalidEmail
  | WeakPassword
  | DatabaseError : String → RegistrationError
  deriving Repr

-- モナド型クラス（副作用を抽象化）
class MyMonad (m : Type → Type) where
  pure : {α : Type} → α → m α
  bind : {α β : Type} → m α → (α → m β) → m β

-- 環境を表現する型クラス（依存性注入のための抽象化）
class MonadUserDb (m : Type → Type) [MyMonad m] where
  checkUserExists : String → m Bool
  saveUser : User → m (Option RegistrationError)

-- 成功または失敗を表現する型
inductive Either (α : Type) (β : Type) where
  | left : α → Either α β
  | right : β → Either α β
  deriving Repr

-- ユーザー登録関数の型シグネチャ
def registerUser {m : Type → Type} [MyMonad m] [MonadUserDb m] 
    (username : String) (email : String) (password : String) 
    : m (Either RegistrationError User) := 
  sorry
#print registerUser
