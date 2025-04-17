def main (args : List String) : IO Unit := do
  let name ← IO.getEnv "USER"
  match name with
  | some username => IO.println s!"現在のユーザー: {username}"
  | none => IO.println "ユーザー名が見つかりません"
