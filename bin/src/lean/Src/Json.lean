def main : IO Unit :=
  IO.FS.writeFile "data.json" "{\"name\": \"Lean4\", \"version\": 4}"
