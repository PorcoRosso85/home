import Src.Logger
import Src.Refer

-- 簡易なJSON型の定義
inductive JsonValue
  | str : String → JsonValue
  | obj : List (String × JsonValue) → JsonValue
  | arr : List JsonValue → JsonValue
  | null : JsonValue

-- JSON文字列変換関数 (終了性の問題を回避するために相互再帰関数を使用)
mutual
  def JsonValue.toString : JsonValue → String
    | .str s => "\"" ++ s ++ "\""
    | .obj fields => "{" ++ JsonValue.objToString fields ++ "}"
    | .arr items => "[" ++ JsonValue.arrToString items ++ "]"
    | .null => "null"
    
  def JsonValue.objToString : List (String × JsonValue) → String
    | [] => ""
    | [(k, v)] => "\"" ++ k ++ "\": " ++ v.toString 
    | (k, v) :: rest => "\"" ++ k ++ "\": " ++ v.toString ++ ", " ++ objToString rest
    
  def JsonValue.arrToString : List JsonValue → String
    | [] => ""
    | [item] => item.toString
    | item :: rest => item.toString ++ ", " ++ arrToString rest
end

-- タスク1: 複数のファイルパス引数を受け取り、拡張子が .lean のみ受け付ける
def filterLeanFiles (files : List String) : List String :=
  files.filter fun file => file.endsWith ".lean"

-- タスク2: ファイル内容の最初の10文字を抽出する関数
-- TODO 1つのファイルパスを受け取り依存関係を解析する関数を適用する
def analyzeFile (filePath : String) : IO String := do
  try
    let content ← IO.FS.readFile filePath
    let analysis := 
      if content.length ≥ 10 then 
        -- String.extract で文字位置を指定するために String.Pos を使用
        let pos10 : String.Pos := ⟨10⟩
        content.extract ⟨0⟩ pos10
      else content
    -- TODO: 本来1つのファイルパスを受け取り依存関係を解析する関数を適用するはず
    return analysis
  catch
    | e => return s!"Error reading file {filePath}: {e.toString}"

-- タスク3: ファイルごとにJSONオブジェクトを作成
def fileToJson (filePath : String) (analysis : String) : JsonValue :=
  JsonValue.obj [
    ("path", JsonValue.str filePath),
    ("analysis", JsonValue.str analysis)
  ]

-- タスク4: ファイルの配列としたJSONを生成
def filesToJsonArray (filesData : List (String × String)) : JsonValue :=
  JsonValue.arr (filesData.map fun (path, analysis) => fileToJson path analysis)

-- メイン関数
def main (args : List String) : IO Unit := do
  let leanFiles := filterLeanFiles args
  
  if leanFiles.isEmpty then
    IO.println "No .lean files provided. Please provide at least one .lean file path."
    return
  
  -- ファイル解析の結果を収集
  let mut filesData := #[]
  for file in leanFiles do
    let analysis ← analyzeFile file
    filesData := filesData.push (file, analysis)
  
  -- ファイルデータからJSONを生成
  let jsonResult := filesToJsonArray filesData.toList
  
  -- タスクx: 標準出力
  IO.println (jsonResult.toString)
