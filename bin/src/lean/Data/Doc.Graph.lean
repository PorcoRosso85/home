import Lean
open Lean Elab Command Term Meta
open Lean.Parser

structure Requirement where
  title : String
  depends : List Requirement

instance : ToMessageData Requirement where
  toMessageData req := m!"Requirement: {req.title}" -- 表示したい内容をカスタマイズできます

def makeRequirement (title : String) (depends : List Requirement) : Requirement :=
  { title := title, depends := depends }

def userType : Requirement := makeRequirement "User型定義" []
def structuring : Requirement := makeRequirement "型定義" [
  userType
]
def queryString : Requirement := makeRequirement "クエリ文字列定義" []
def queryable : Requirement := makeRequirement "格納された情報をクエリ可能" [
  queryString
]

def ask : Requirement := makeRequirement
"目的は
型クラスについて知ること
ドキュメントの説明を簡単にしてほしい
"
[]
def purpose : Requirement := makeRequirement "目的" [
  -- structuring,
  -- queryable,
  ask,
]

def getDependencies (req : Requirement) (n : Nat) : Requirement :=
  if n = 0 then { title := req.title, depends := [] }
  else { title := req.title, depends := req.depends.map (fun dep => getDependencies dep (n - 1)) }
#eval getDependencies purpose 1


/-
目的は
ある定義(userType)を引数と与えたとき, それに依存するstructuringやpurposeなどを取得したい
結果的にmakeRequirementによる依存関係の表現（正のベクトル）が負のベクトルによる探索を自動化することで必要以上の記述を抑えられたらよい
TODOプラン
1. **Requirementの定義をメタデータとして解析する** Reflection使用案
   - `Doc.Graph.lean` をメタプログラミングで読み込み、`Requirement` の定義 (特に `depends` フィールド) を `Syntax` または `Expr` として解析します。
   - 各 `Requirement` の `title` と `depends` の情報を抽出し、データ構造 (例えば Map) に格納します。
   - データ構造を、**各 `Requirement` の `title` をキー**とし、**その `Requirement` に依存する `Requirement` の `title` のリストを値**とするMapとして構築し、目的の `Requirement` の `title` をキーとして、Mapから依存元のリストを取得する関数をメタプログラミングで実装します。

2. **コンパイル時に依存関係グラフを構築するマクロを作成する**:
   - `Requirement` を定義する際に、依存関係を自動的に記録するようなマクロを作成します。
   - マクロは、`Requirement` が定義されるたびに、その `title` をキーとし、**その `Requirement` に依存する `Requirement` の `title` のリスト** を値とする内 部的なデータ構造に記録します。
   - 依存関係を問い合わせるコマンド (例: `#showDependencies <Requirementのtitle>`) を `Elab` で作成し、記録されたデータ構造から**指定された `Requirement`  に依存する `Requirement` の `title` のリスト** を表示するようにします。


第３案 型クラス仕様案？
instances
https://lean-lang.org/doc/reference/latest/Type-Classes/
`makeRequirement` を使った依存関係の記述は、直感的ではありますが、より宣言的に、そして簡潔に依存関係を表現する方法として、**型クラス** を利用することを提案します。
Leanの型クラスは、**インターフェース** のような役割を果たし、特定の型が満たすべき性質や操作を定義できます。これを利用して、`Requirement` 間の依存関係を型クラスのインスタンスとして表現することができます。
まず、`HasDependency` という型クラスを定義します。これは、ある `Requirement` (`FromReq`) が別の `Requirement` (`ToReq`) に依存していることを表す型クラスです。
```lean
class HasDependency (FromReq : Type) (ToReq : Type) where
  -- 特にメソッドは定義しない。依存関係の存在を示すマーカー型クラスとして使用
```

次に、`HasDependency` のインスタンスを宣言することで、`Requirement` 間の依存関係を記述します。
```lean
instance : HasDependency structuring userType := {}
instance : HasDependency purpose structuring := {}
instance : HasDependency purpose queryable := {}
instance : HasDependency purpose ask := {}
```

このようにインスタンスを宣言することで、`structuring` は `userType` に依存し、`purpose` は `structuring`, `queryable`, `ask` に依存している、という関係を型システムに登録できます。
そして、この型クラスと**型クラスのインスタンス探索機構**を利用して、特定の `Requirement` に依存する全ての `Requirement` を自動的に取得する関数 `findDependencies` を実装します。
```lean
def findDependencies [HasDependency fromReq toReq] (from : fromReq) : List toReq :=
  [ (default : toReq) ]

-- 型クラスのインスタンスを再帰的に探索して依存関係を取得する関数
def findAllDependencies [Inhabited Requirement] (reqTitle : String) : MetaM (List Requirement) := do
  let structuring ← liftMetaM <| findConst `structuring
  let queryable ← liftMetaM <| findConst `queryable
  let userType ← liftMetaM <| findConst `userType
  let ask ← liftMetaM <| findConst `ask
  let purpose ← liftMetaM <| findConst `purpose

  if reqTitle == "userType" then
    return []
  else if reqTitle == "structuring" then
    return [userType]
  else if reqTitle == "purpose" then
    return [structuring, queryable, ask]
  else
    return []

#eval findAllDependencies "userType"
#eval findAllDependencies "structuring"
#eval findAllDependencies "purpose"
```
-/


/-
class HasDependency (FromReq : Type) (ToReq : Type) where

instance : HasDependency structuring userType := {}
instance : HasDependency purpose structuring := {}
instance : HasDependency purpose queryable := {}
instance : HasDependency purpose ask := {}

def findDependencies [HasDependency fromReq toReq] (from : fromReq) : List toReq :=
  [ (default : toReq) ]

-- 型クラスのインスタンスを再帰的に探索して依存関係を取得する関数
def findAllDependencies [Inhabited Requirement] (reqTitle : String) : MetaM (List Requirement) := do
  let structuring ← liftMetaM <| findConst `structuring
  let queryable ← liftMetaM <| findConst `queryable
  let userType ← liftMetaM <| findConst `userType
  let ask ← liftMetaM <| findConst `ask
  let purpose ← liftMetaM <| findConst `purpose

  if reqTitle == "userType" then
    return []
  else if reqTitle == "structuring" then
    return [userType]
  else if reqTitle == "purpose" then
    return [structuring, queryable, ask]
  else
    return []

#eval findAllDependencies "userType"
#eval findAllDependencies "structuring"
#eval findAllDependencies "purpose"
-/
