/-
# Expressions

Expressions (terms of type `Expr`) are an abstract syntax tree for Lean programs.
This means that each term which can be written in Lean has a corresponding `Expr`.
For example, the application `f e` is represented by the expression `Expr.app ⟦f⟧ ⟦e⟧`,
where `⟦f⟧` is a representation of `f` and `⟦e⟧` a representation of `e`.
Similarly, the term `Nat` is represented by the expression ``Expr.const `Nat []``.
(The backtick and empty list are discussed below.)

The ultimate purpose of a Lean tactic block
is to generate a term which serves as a proof of the theorem we want to prove.
Thus, the purpose of a tactic is to produce (part of) an `Expr` of the right type.
Much metaprogramming therefore comes down to manipulating expressions:
constructing new ones and taking apart existing ones.

Once a tactic block is finished, the `Expr` is sent to the kernel,
which checks whether it is well-typed and whether it really has the type claimed by the theorem.
As a result, tactic bugs are not fatal:
if you make a mistake, the kernel will ultimately catch it.
However, many internal Lean functions also assume that expressions are well-typed,
so you may crash Lean before the expression ever reaches the kernel.
To avoid this, Lean provides many functions which help with the manipulation of expressions.
This chapter and the next survey the most important ones.

Let's get concrete and look at the
[`Expr`](https://github.com/leanprover/lean4/blob/master/src/Lean/Expr.lean)
type:
-/

import Lean

namespace Playground

inductive Expr where
  | bvar    : Nat → Expr                              -- bound variables
  | fvar    : FVarId → Expr                           -- free variables
  | mvar    : MVarId → Expr                           -- meta variables
  | sort    : Level → Expr                            -- Sort
  | const   : Name → List Level → Expr                -- constants
  | app     : Expr → Expr → Expr                      -- application
  | lam     : Name → Expr → Expr → BinderInfo → Expr  -- lambda abstraction
  | forallE : Name → Expr → Expr → BinderInfo → Expr  -- (dependent) arrow
  | letE    : Name → Expr → Expr → Expr → Bool → Expr -- let expressions
  -- less essential constructors:
  | lit     : Literal → Expr                          -- literals
  | mdata   : MData → Expr → Expr                     -- metadata
  | proj    : Name → Nat → Expr → Expr                -- projection

end Playground

/-! What is each of these constructors doing?

- `bvar` is a __bound variable__.
  For example, the `x` in `fun x => x + 2` or `∑ x, x²`.
  This is any occurrence of a variable in an expression where there is a binder above it.
  Why is the argument a `Nat`? This is called a de Bruijn index and will be explained later.
  You can figure out the type of a bound variable by looking at its binder,
  since the binder always has the type information for it.
- `fvar` is a __free variable__.
  These are variables which are not bound by a binder.
  An example is `x` in `x + 2`.
  Note that you can't just look at a free variable `x` and tell what its type is,
  there needs to be a context which contains a declaration for `x` and its type.
  A free variable has an ID that tells you where to look for it in a `LocalContext`.
  In Lean 3, free variables were called "local constants" or "locals".
- `mvar` is a __metavariable__.
  There will be much more on these later,
  but you can think of it as a placeholder or a 'hole' in an expression
  that needs to be filled at a later point.
- `sort` is used for `Type u`, `Prop` etc.
- `const` is a constant that has been defined earlier in the Lean document.
- `app` is a function application.
  Multiple arguments are done using _partial application_: `f x y ↝ app (app f x) y`.
- `lam n t b` is a lambda expression (`fun ($n : $t) => $b`).
  The `b` argument is called the __body__.
  Note that you have to give the type of the variable you are binding.
- `forallE n t b` is a dependent arrow expression (`($n : $t) → $b`).
  This is also sometimes called a Π-type or Π-expression
  and is often written `∀ $n : $t, $b`.
  Note that the non-dependent arrow `α → β` is a special case of `(a : α) → β`
  where `β` doesn't depend on `a`.
  The `E` on the end of `forallE` is to distinguish it from the `forall` keyword.
- `letE n t v b` is a __let binder__ (`let ($n : $t) := $v in $b`).
- `lit` is a __literal__, this is a number or string literal like `4` or `"hello world"`.
  Literals help with performance:
  we don't want to represent the expression `(10000 : Nat)`
  as `Nat.succ $ ... $ Nat.succ Nat.zero`.
- `mdata` is just a way of storing extra information on expressions that might be useful,
  without changing the nature of the expression.
- `proj` is for projection.
  Suppose you have a structure such as `p : α × β`,
  rather than storing the projection `π₁ p` as `app π₁ p`, it is expressed as `proj Prod 0 p`.
  This is for efficiency reasons ([todo] find link to docstring explaining this).

You've probably noticed
that you can write many Lean programs which do not have an obvious corresponding `Expr`.
For example, what about `match` statements, `do` blocks or `by` blocks?
These constructs, and many more, must indeed first be translated into expressions.
The part of Lean which performs this (substantial) task is called the elaborator
and is discussed in its own chapter.
The benefit of this setup is that once the translation to `Expr` is done,
we have a relatively simple structure to work with.
(The downside is that going back from `Expr` to a high-level Lean program can be challenging.)

The elaborator also fills in any implicit or typeclass instance arguments
which you may have omitted from your Lean program.
Thus, at the `Expr` level, constants are always applied to all their arguments, implicit or not.
This is both a blessing
(because you get a lot of information which is not obvious from the source code)
and a curse
(because when you build an `Expr`, you must supply any implicit or instance arguments yourself).

## De Bruijn Indexes

Consider the lambda expression `(λ x : ℕ => λ y : ℕ => x + y) y`.
When we evaluate it naively, by replacing `x` with `y` in the body of the outer lambda, we obtain `λ y : ℕ => y + y`.
But this is incorrect: the lambda is a function with two arguments that adds one argument to the other, yet the evaluated version adds its argument to itself.
The root of the issue is that the name `y` is used for both the variable outside the lambdas and the variable bound by the inner lambda.
Having different variables use the same name means that when we evaluate, or β-reduce, an application, we must be careful not to confuse the different variables.

To address this issue, Lean does not, in fact, refer to bound variables by name.
Instead, it uses __de Bruijn indexes__.
In de Bruijn indexing,
each variable bound by a `lam` or a `forallE` is converted into a number `#n`.
The number says how many binders up the `Expr` tree we should skip
to find the binder that binds this variable.
So our above example would become
(replacing inessential parts of the expression with `_` for brevity):
```
app (lam `x _ (lam `y _ (app (app `plus #1) #0) _) _) (fvar _)
```
The `fvar` represents `y` and the lambdas' variables are now represented by `#0` and `#1`.
When we evaluate this application, we replace the bound variable belonging to ``lam `x`` (here `#1`) with the argument `fvar _`, obtaining
```
(lam `y _ (app (app `plus (fvar _)) #0) _)
```
This is pretty-printed as
```
λ y_1 => y + y_1
```
Note that Lean has automatically chosen a name `y_1` for the remaining bound variable that does not clash with the name of the `fvar` `y`.
The chosen name is based on the name suggestion `y` contained in the `lam`.

If a de Bruijn index is too large for the number of binders preceding it,
we say it is a __loose `bvar`__;
otherwise we say it is __bound__.
For example, in the expression ``lam `x _ (app #0 #1)``
the `bvar` `#0` is bound by the preceding binder and `#1` is loose.
The fact that Lean calls all de Bruijn indexes `bvar`s ("bound variables")
points to an important invariant:
outside of some very low-level functions,
Lean expects that expressions do not contain any loose `bvar`s.
Instead, whenever we would be tempted to introduce a loose `bvar`,
we immediately convert it into an `fvar` ("free variable").
(Hence, Lean's binder representation is "locally nameless".)
Precisely how that works is discussed in the next chapter.

If there are no loose `bvar`s in an expression, we say that the expression is __closed__.
The process of replacing all instances of a loose `bvar` with an `Expr`
is called __instantiation__.
Going the other way is called __abstraction__.

If you are familiar with the standard terminology around variables,
Lean's terminology may be confusing,
so here's a map:
Lean's "bvars" are usually called just "variables";
Lean's "loose" is usually called "free";
and Lean's "fvars" might be called "local hypotheses".

## Universe Levels

Some expressions involve universe levels, represented by the `Lean.Level` type.
A universe level is a natural number,
a universe parameter (introduced with a `universe` declaration),
a universe metavariable or the maximum of two universes.
They are relevant for two kinds of expressions.

First, sorts are represented by `Expr.sort u`, where `u` is a `Level`.
`Prop` is `sort Level.zero`; `Type` is `sort (Level.succ Level.zero)`.

Second, universe-polymorphic constants have universe arguments.
A universe-polymorphic constant is one whose type contains universe parameters.
For example, the `List.map` function is universe-polymorphic,
as the `pp.universes` pretty-printing option shows:
-/

set_option pp.universes true in
#check @List.map

/-!
The `.{u_1,u_2}` suffix after `List.map`
means that `List.map` has two universe arguments, `u_1` and `u_2`.
The `.{u_1}` suffix after `List` (which is itself a universe-polymorphic constant)
means that `List` is applied to the universe argument `u_1`, and similar for `.{u_2}`.

In fact, whenever you use a universe-polymorphic constant,
you must apply it to the correct universe arguments.
This application is represented by the `List Level` argument of `Expr.const`.
When we write regular Lean code, Lean infers the universes automatically,
so we do not need think about them much.
But when we construct `Expr`s,
we must be careful to apply each universe-polymorphic constant to the right universe arguments.

## Constructing Expressions

### Constants

The simplest expressions we can construct are constants.
We use the `const` constructor and give it a name and a list of universe levels.
Most of our examples only involve non-universe-polymorphic constants,
in which case the list is empty.

We also show a second form where we write the name with double backticks.
This checks that the name in fact refers to a defined constant,
which is useful to avoid typos.
-/

open Lean

def z' := Expr.const `Nat.zero []
#eval z' -- Lean.Expr.const `Nat.zero []

def z := Expr.const ``Nat.zero []
#eval z -- Lean.Expr.const `Nat.zero []

/-
The double-backtick variant also resolves the given name, making it fully-qualified.
To illustrate this mechanism, here are two further examples.
The first expression, `z₁`, is unsafe:
if we use it in a context where the `Nat` namespace is not open,
Lean will complain that there is no constant called `zero` in the environment.
In contrast, the second expression, `z₂`,
contains the fully-qualified name `Nat.zero` and does not have this problem.
-/

open Nat

def z₁ := Expr.const `zero []
#eval z₁ -- Lean.Expr.const `zero []

def z₂ := Expr.const ``zero []
#eval z₂ -- Lean.Expr.const `Nat.zero []

/-
### Function Applications

The next class of expressions we consider are function applications.
These can be built using the `app` constructor,
with the first argument being an expression for the function
and the second being an expression for the argument.

Here are two examples.
The first is simply a constant applied to another.
The second is a recursive definition giving an expression as a function of a natural number.
-/

def one := Expr.app (.const ``Nat.succ []) z
#eval one
-- Lean.Expr.app (Lean.Expr.const `Nat.succ []) (Lean.Expr.const `Nat.zero [])

def natExpr: Nat → Expr
| 0     => z
| n + 1 => .app (.const ``Nat.succ []) (natExpr n)

/-
Next we use the variant `mkAppN` which allows application with multiple arguments.
-/

def sumExpr : Nat → Nat → Expr
| n, m => mkAppN (.const ``Nat.add []) #[natExpr n, natExpr m]

/-
As you may have noticed, we didn't show `#eval` outputs for the two last functions.
That's because the resulting expressions can grow so large
that it's hard to make sense of them.

### Lambda Abstractions

We next use the constructor `lam`
to construct a simple function which takes any natural number `x` and returns `Nat.zero`.
The argument `BinderInfo.default` says that `x` is an explicit argument
(rather than an implicit or typeclass argument).
-/

def constZero : Expr :=
  .lam `x (.const ``Nat []) (.const ``Nat.zero []) BinderInfo.default

#eval constZero
-- Lean.Expr.lam `x (Lean.Expr.const `Nat []) (Lean.Expr.const `Nat.zero [])
--   (Lean.BinderInfo.default)

/-!
As a more elaborate example which also involves universe levels,
here is the `Expr` that represents `List.map (λ x => Nat.add x 1) []`
(broken up into several definitions to make it somewhat readable):
-/

def nat : Expr := .const ``Nat []

def addOne : Expr :=
  .lam `x nat
    (mkAppN (.const ``Nat.add []) #[.bvar 0, mkNatLit 1])
    BinderInfo.default

def mapAddOneNil : Expr :=
  mkAppN (.const ``List.map [levelZero, levelZero])
    #[nat, nat, addOne, .app (.const ``List.nil [levelZero]) nat]

/-!
With a little trick (more about which in the Elaboration chapter),
we can turn our `Expr` into a Lean term, which allows us to inspect it more easily.
-/

elab "mapAddOneNil" : term => return mapAddOneNil

#check mapAddOneNil
-- List.map (fun x => Nat.add x 1) [] : List Nat

set_option pp.universes true in
set_option pp.explicit true in
#check mapAddOneNil
-- @List.map.{0, 0} Nat Nat (fun x => x.add 1) (@List.nil.{0} Nat) : List.{0} Nat

#reduce mapAddOneNil
-- []

/-
In the next chapter we explore the `MetaM` monad,
which, among many other things,
allows us to more conveniently construct and destruct larger expressions.

## Exercises

1. Create expression `1 + 2` with `Expr.app`.
2. Create expression `1 + 2` with `Lean.mkAppN`.
3. Create expression `fun x => 1 + x`.
4. [**De Bruijn Indexes**] Create expression `fun a, fun b, fun c, (b * a) + c`.
5. Create expression `fun x y => x + y`.
6. Create expression `fun x, String.append "hello, " x`.
7. Create expression `∀ x : Prop, x ∧ x`.
8. Create expression `Nat → String`.
9. Create expression `fun (p : Prop) => (λ hP : p => hP)`.
10. [**Universe levels**] Create expression `Type 6`.
-/

-- 1. Create expression `1 + 2` with `Expr.app`.
-- 1. **`Expr.app` で `1 + 2`:**  `Nat.add` 関数を `Expr.const ``Nat.add []` で表現し、`mkNatLit 1` と `mkNatLit 2` を引数として `Expr.app` を2回ネストして適用します。
def ex1_1: Expr := Expr.app (Expr.app (Expr.const ``Nat.add []) (mkNatLit 1)) (mkNatLit 2)
#eval ex1_1
elab "ex1_1": term => return ex1_1
#check ex1_1
#eval ex1_1

-- 2. Create expression `1 + 2` with `Lean.mkAppN`.
-- 2. **`Lean.mkAppN` で `1 + 2`:**  `mkAppN` は複数の引数を一度に適用できるため、`Nat.add` 関数と引数 `1` と `2` をリスト `#[mkNatLit 1, mkNatLit 2]` にまとめて `mkAppN` に渡します。より簡潔に記述できます。
def ex1_2 : Expr := mkAppN (Expr.const ``Nat.add []) #[mkNatLit 1, mkNatLit 2]
#eval ex1_2
elab "ex1_2": term => return ex1_2
#check ex1_2
#eval ex1_2

-- 3. Create expression `fun x => 1 + x`.
-- 3. **`fun x => 1 + x`:**  `Expr.lam` を使用してラムダ抽象を構築します。変数名 `x`、型 `Nat` (`Expr.const ``Nat []`)、本体 `1 + x` (`mkAppN ... Expr.bvar 0`)、BinderInfo (`BinderInfo.default`) を指定します。 `Expr.bvar 0` は、一番内側のラムダで束縛された変数 (ここ では `x`) をDe Bruijn indexで参照しています。
def ex1_3 : Expr :=
  Expr.lam `x (Expr.const ``Nat [])
    (mkAppN (Expr.const ``Nat.add []) #[mkNatLit 1, Expr.bvar 0])
    BinderInfo.default
#eval ex1_3
elab "ex1_3": term => return ex1_3
#check ex1_3
#eval ex1_3 10

-- 4. [**De Bruijn Indexes**] Create expression `fun a, fun b, fun c, (b * a) + c`.
-- 4. **`fun a, fun b, fun c, (b * a) + c`:** 3つのネストされた `Expr.lam` を使用します。De Bruijn index を正しく使用することが重要です。`b` は2つ外側のラムダで束縛されているため `Expr.bvar 1`、 `a` は3つ外側のラムダで束縛されているため `Expr.bvar 2`、 `c` は一番内側のラムダで束縛されているため `Expr.bvar 0` を使用します。
-- def ex1_4 : Expr :=
--   Expr.lam `a (Expr.const ``Nat []) $
--   Expr.lam `b (Expr.const ``Nat []) $
--   Expr.lam `c (Expr.const ``Nat []) $
--     mkAppN (Expr.const ``Nat.add []) #[
--       mkAppN (Expr.const ``Nat.mul []) #[Expr.bvar 1, Expr.bvar 2],
--       Expr.bvar 0
--     ]
--     BinderInfo.default
--     BinderInfo.default
--     BinderInfo.default

-- 5. **`fun x y => x + y`:** 2つのネストされた `Expr.lam` を使用します。`x` は外側のラムダで束縛されているため `Expr.bvar 1`、 `y` は 内側のラムダで束縛されているため `Expr.bvar 0` を使用します。
-- 5. Create expression `fun x y => x + y`.
def ex1_5 : Expr :=
  Expr.lam `x (Expr.const ``Nat [])
    (Expr.lam `y (Expr.const ``Nat [])
      (mkAppN (Expr.const ``Nat.add []) #[Expr.bvar 1, Expr.bvar 0])
      BinderInfo.default)
    BinderInfo.default
#eval ex1_5
elab "ex1_5": term => return ex1_5
#check ex1_5
#eval ex1_5 3 4

-- 6. **`fun x, String.append "hello, " x`:**  `String.append` 関数と文字列リテラル `"hello, "` を使用します。文字列リテラルは `Expr.lit (Literal.strVal "hello, ")` で表現します。
-- 6. Create expression `fun x, String.append "hello, " x`.
def ex1_6 : Expr :=
  Expr.lam `x (Expr.const ``String []) 
    (mkAppN (Expr.const ``String.append []) #[
      Expr.lit (Literal.strVal "hello, "),
      Expr.bvar 0
    ])
    BinderInfo.default
#eval ex1_6
elab "ex1_6": term => return ex1_6
#check ex1_6
#eval ex1_6 "world!"



-- 7. Create expression `∀ x : Prop, x ∧ x`.
-- 7. **`∀ x : Prop, x ∧ x`:**  全称量化 `∀` は `Expr.forallE` で表現します。変数名 `x`、型 `Prop` (`Expr.sort Level.prop`)、本体 `x ∧ x` (`mkAppN ... Expr.bvar 0`)、BinderInfo (`BinderInfo.default`) を指定します。
def ex1_7 : Expr :=
  Expr.forallE `x (Expr.sort Level.zero)
    (mkAppN (Expr.const ``And []) #[Expr.bvar 0, Expr.bvar 0])
    BinderInfo.default
#eval ex1_7
elab "ex1_7": term => return ex1_7
#check ex1_7

-- 8. Create expression `Nat → String`.
-- 8. **`Nat → String`:**  非依存関数型 (non-dependent arrow) も `Expr.forallE` で表現します。変数名は `_` (匿名変数)、引数の型 `Nat`、返り値の型 `String` を指定します。
def ex1_8 : Expr :=
  Expr.forallE `_ (Expr.const ``Nat []) (Expr.const ``String []) BinderInfo.default
#eval ex1_8
elab "ex1_8": term => return ex1_8
#check ex1_8

-- 9. Create expression `fun (p : Prop) => (λ hP : p => hP)`.
-- 9. **`fun (p : Prop) => (λ hP : p => hP)`:** ネストされたラムダ抽象です。外側のラムダで `p : Prop` を束縛し、内側のラムダで `hP : p` を束縛しています。内側のラムダの本体は `hP` (`Expr.bvar 0`) です。
def ex1_9 : Expr :=
  Expr.lam `p (Expr.sort Level.zero)
  (Expr.lam `hP (Expr.bvar 0) (Expr.bvar 0) BinderInfo.default)
  BinderInfo.default
#eval ex1_9
elab "ex1_9": term => return ex1_9
#check ex1_9

-- 10. [**Universe levels**] Create expression `Type 6`.
-- 10. **`Type 6`:**  `Type u` は `Expr.sort u` で表現します。`Type 6` は `Expr.sort Level.succ (Level.succ ... Level.zero)` のように `Level.succ` を6回適用して構築します。
def ex1_10 : Expr :=
  Expr.sort (Level.succ (Level.succ (Level.succ (Level.succ (Level.succ (Level.succ Level.zero))))))
#eval ex1_10
elab "ex1_10": term => return ex1_10
#check ex1_10

