import Lean
import Src.Logger

open Lean Meta Elab Command

inductive Job | mk : Job
inductive Where | mk : Where
inductive Email | mk : Email

inductive Greeting
| mk (_where : Where) (job : Job) : Greeting

inductive About
| mk (email : Email) : About

inductive Intro
| mk (greeting : Greeting) (about : About) : Intro

inductive Blog
| mk (intro : Intro) : Blog

/-- Get the type dependencies for an inductive type -/
def getInductiveTypeDeps (declName : Name) : MetaM (List Name) := do
  match (← getEnv).find? declName with
  | none => pure []
  | some (ConstantInfo.inductInfo val) =>
    let mut deps : List Name := []
    for ctor in val.ctors do
      let type ← inferType (mkConst ctor)
      -- Traverse the type expression to find dependencies
      let mut curr := type
      while curr.isArrow do
        let dom := curr.bindingDomain!
        logDebug s!"  Processing domain: {dom}"
        match dom.constName? with
        | some depName =>
            if depName != declName then -- 追加: 型自身を依存関係に入れない
              deps := depName :: deps
              logDebug s!"    Added dependency (domain): {depName}"
            else logDebug s!"    Skipping self-dependency (domain): {depName}"
        | none => pure ()
        curr := curr.bindingBody!
        logDebug s!"  Processing body: {curr}"
      match curr.constName? with
      | some depName =>
          if depName != declName then -- 追加: 型自身を依存関係に入れない
            deps := depName :: deps
            logDebug s!"    Added dependency (body): {depName}"
          else logDebug s!"    Skipping self-dependency (body): {depName}"
      | none => pure ()
    let result := deps.eraseDups; logDebug s!"  Dependencies for {declName}: {result}"; return result
  | _ => pure []


-- 単一の型に対してテスト
#eval show MetaM Unit from do
  let deps ← getInductiveTypeDeps `Greeting
  IO.println s!"Greeting: {deps}"
  let deps ← getInductiveTypeDeps `Blog
  IO.println s!"Blog: {deps}"

/--
Recursively get inductive type dependencies up to a specified depth.

Example output (for depth = 2):
HashMap.fromList [
  (`Blog, [`Intro]),        -- Blog depends on Intro
  (`Intro, [`Greeting, `About]), -- Intro depends on Greeting and About
  (`Greeting, [`Where, `Job]), -- Greeting depends on Where and Job
  (`About, [`Email])         -- About depends on Email
]
-/
def getReferees (declName : Name) (depth : Nat) : MetaM (Std.HashMap Name (List Name)) := do
  -- logDebug s!"getInductiveTypeDepsUpToDepth called with declName: {declName}, depth: {depth}"
  let mut allDepsMap : Std.HashMap Name (List Name) := Std.HashMap.empty
  let mut toProcess : List (Name × Nat) := [(declName, 0)]

  while !toProcess.isEmpty do
    let (name, currentDepth) := toProcess.head!
    toProcess := toProcess.tail!

    if currentDepth < depth then
      logDebug s!"Processing name: {name}, currentDepth: {currentDepth}"
      let deps ← getInductiveTypeDeps name
      logDebug s!"Dependencies of {name}: {deps}"
      allDepsMap := allDepsMap.insert name deps
      for dep in deps do
        toProcess := (dep, currentDepth + 1) :: toProcess
      -- logDebug s!"Updated allDepsMap: {allDepsMap}"

  return allDepsMap


#eval show MetaM Unit from do
  let refereesMap ← getReferees `Blog 2
  for (name, deps) in refereesMap.toList do
    IO.println s!"{name}: {deps}"


/-
/--
  Std.HashMap Name (List Name) を受け取り、(Name, List Name) のペアのリストを返す。
  リストは Name (キー) に基づいてソートされている。
-/
def sortReferees (refereesMap : Std.HashMap Name (List Name)) : List (Name × List Name) :=
  let listOfPairs := refereesMap.toList
  listOfPairs.sort (λ (name1, _) (name2, _) => compare name1 name2)

/--
  Std.HashMap Name (List Name) を受け取り、(Name, List Name) のペアのリストを返す。
  リストは、依存関係のリストの長さに基づいてソートされている。
-/
def sortRefereesByDepLength (refereesMap : Std.HashMap Name (List Name)) : List (Name × List Name) :=
  let listOfPairs := refereesMap.toList
  listOfPairs.sort (λ (_, deps1) (_, deps2) => compare deps1.length deps2.length)

 -- 使用例 (getReferees の結果をソート)
 #eval show MetaM Unit from do
   let refereesMap ← getReferees `Blog 4
   let sortedByName := sortReferees refereesMap
   IO.println "Sorted by Name:"
   for (name, deps) in sortedByName do
     IO.println s!"{name}: {deps}"

   let sortedByDepLength := sortRefereesByDepLength refereesMap
   IO.println "\nSorted by Dependency Length:"
   for (name, deps) in sortedByDepLength do
     IO.println s!"{name}: {deps}"

-/

/-
どの型に依存されているか再帰的に取得する
Recursively get the types that depend on a given inductive type, up to a specified depth.
-/
def getInductiveTypeReferersUpToDepth (declName : Name) (depth : Nat) : MetaM (List Name) := do
  logDebug s!"getInductiveTypeReferersUpToDepth called with declName: {declName}, depth: {depth}"
  let mut allReferers : List Name := []
  let mut toProcess : List (Name × Nat) := [(declName, 0)]

  while !toProcess.isEmpty do
    logDebug s!"toProcess: {toProcess}"
    logDebug s!"allReferers: {allReferers}"
    let toProcessHead := toProcess.head!
    let (name, currentDepth) := toProcess.head!
    toProcess := toProcess.tail!

    if currentDepth < depth then
      logDebug s!"Processing name: {name}, currentDepth: {currentDepth}"
      let mut referers : List Name := []
      let env ← getEnv
      for (declName, constInfo) in env.constants.toList do
        -- logDebug s!"Checking constant: {declName}"
        match constInfo with
        | ConstantInfo.inductInfo val =>
          if val.name.toString.startsWith "Lean." then
            continue
          let deps ← getInductiveTypeDeps declName
          -- logDebug s!"Deps of {declName} : {deps}"
          if deps.contains name then
            logInfo s!"{declName} refers to {name}"
            logDebug s!"{declName} refers to {name}"
            referers := declName :: referers
        | _ =>
          pure ()
      logDebug s!"referers of {name} : {referers}"
      allReferers := (name :: referers) ++ allReferers
      -- logDebug s!"Updated allReferers: {allReferers}" -- コメントアウト
      for referer in referers do
        logDebug s!"Adding to toProcess: {(referer, currentDepth + 1)}"  -- 追加
        toProcess := (referer, currentDepth + 1) :: toProcess
    else do
      logDebug s!"Skipping {toProcessHead} because currentDepth {currentDepth} >= depth {depth}"

  return allReferers.eraseDups


-- TODO
-- #eval show MetaM _ from do
--   let referers ← getInductiveTypeReferersUpToDepth `Job 3
--   logInfo s!"Referers of Job: {referers}"


