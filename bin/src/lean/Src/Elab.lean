import Lean

open Lean Elab Command Term Meta


syntax (name := mycommand1) "#mycommand1" : command -- declare the syntax
@[command_elab mycommand1]
def mycommand1Impl : CommandElab := fun stx => do -- declare and register the elaborator
  logInfo "Hello World"
#mycommand1 -- Hello World


elab "#mycommand2" : command =>
  logInfo "Hello World"
#mycommand2


elab "#check" "mycheck" : command => do
  logInfo "Got ya!"
#check mycheck


@[command_elab Lean.Parser.Command.check] def mySpecialCheck : CommandElab := fun stx => do
  if let some str := stx[1].isStrLit? then
    logInfo s!"Specially elaborated string literal!: {str} : String"
  else
    throwUnsupportedSyntax
#check "hello"


elab "#findCElab " c:command : command => do
  let macroRes ← liftMacroM <| expandMacroImpl? (←getEnv) c
  match macroRes with
  | some (name, _) => logInfo s!"Next step is a macro: {name.toString}"
  | none =>
    let kind := c.raw.getKind
    let elabs := commandElabAttribute.getEntries (←getEnv) kind
    match elabs with
    | [] => logInfo s!"There is no elaborators for your syntax, looks like its bad :("
    | _ => logInfo s!"Your syntax may be elaborated by: {elabs.map (fun el => el.declName.toString)}"
#findCElab open ar
#findCElab def lala := 12
#findCElab abbrev lolo := 12
#findCElab #check foo
#findCElab open Hi
#findCElab open Bar
#findCElab namespace Foo


elab "#shell_ls" : command => do
  let spawn_args: IO.Process.SpawnArgs := {cmd := "ls", args := #["-l"]}
  let output <- IO.Process.output spawn_args
  logInfo output.stdout
#shell_ls


elab "#shell" s:str+ : command => do
  let cmds := s.map TSyntax.getString
  let (cmd, args) := (cmds[0]!, cmds[1:])
  let cmd: IO.Process.SpawnArgs := {cmd, args}
  let output <- IO.Process.output cmd
  logInfo output.stdout
#shell "ls" "-l"
