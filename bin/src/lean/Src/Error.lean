import Lean
import Src.Refer
open Lean Meta

inductive ApplyError : Type where
  | invalidInput
  | divisionByZero
  deriving Repr

instance : ToString ApplyError where
  toString e := toString (repr e)

--  Updated to include an error case
inductive Devided : Type where
| mk (n : Nat) : Devided
| err (e : ApplyError) : Devided

--  Repr instance for Devided
instance : Repr Devided where
  reprPrec d _ := match d with
    | Devided.mk n => s!"Devided.mk {n}"
    | Devided.err e => s!"Devided.err {e}"

--  New function to perform division, returning Devided
def safeDiv (n1 : Nat) (n2 : Nat) : Devided :=
  if n2 = 0 then
    Devided.err ApplyError.divisionByZero
  else
    Devided.mk (n1 / n2)

-- Example usage and tests.
#eval safeDiv 10 2
#eval safeDiv 10 0

inductive TriangleArea : Nat -> Nat -> Type where
  | mk (base height : Nat) (devided : Devided) : TriangleArea base height

-- 上記のように型を変更したとき, この関数はどう変更される？ ai!
def triangleArea (base height : Nat) : TriangleArea base height :=
    TriangleArea.mk base height (safeDiv (base * height) 2)
#eval triangleArea 5 4
