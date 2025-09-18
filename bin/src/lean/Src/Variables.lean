import Lean

open Lean System

def getDebugEnv : IO String := do
    let env ← IO.getEnv "DEBUG"
    match env with
    | some value => return value
    -- TODO
    -- | none => throw (IO.Error.userError "DEBUG environment variable not found")
    | none => return ""

def getDebug : IO Bool := do
  let val ← getDebugEnv
  return (val.toLower == "true")
#eval getDebug
