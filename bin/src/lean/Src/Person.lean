import Lean

inductive PersonCreationError where
  | invalidName : PersonCreationError
  | invalidAge : PersonCreationError
  | unknown : PersonCreationError

inductive Person where
  | mk (name : String) (age : Nat) : Person
  | err (e : PersonCreationError) : Person

-- 名前を生成する外部関数（例）
def generateName : String :=
  "John Doe" -- 例として固定の名前を返します。

def createPerson (age : Nat) : Person := 
  let name := generateName
  if String.isEmpty name then
    Person.err PersonCreationError.invalidName
  else if age > 150 then -- 例として年齢の上限を設定
    Person.err PersonCreationError.invalidAge
  else
    Person.mk name age

def main : IO Unit := do
  let person1 := createPerson 30
  let person2 := createPerson 200 -- エラーになるケース

  match person1 with
  | Person.mk name age =>
    IO.println s!"Person 1: Name = {name}, Age = {age}"
  | Person.err e =>
    IO.println s!"Person 1 creation error: {e}"

  match person2 with
  | Person.mk name age =>
    IO.println s!"Person 2: Name = {name}, Age = {age}"
  | Person.err e =>
    IO.println s!"Person 2 creation error: {e}"
