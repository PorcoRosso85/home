import Src.Variables

def logDebug (msg : String) : IO Unit := do
  -- TODO
  if (← getDebug) then
    IO.println s!"[DEBUG] {msg}"
  else
    pure ()

#eval logDebug "This is a debug message."

