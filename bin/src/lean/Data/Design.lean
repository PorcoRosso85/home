import Src.Refer
open Lean

-- 依存関係を取得する機能
inductive GetInductiveTypeDeps : Type where
| mk : GetInductiveTypeDeps

-- 依存関係を再帰的に取得する機能
inductive GetReferees : Type where
| mk : GetReferees

-- 参照元を再帰的に取得する機能
inductive GetInductiveTypeReferersUpToDepth : Type where
| mk : GetInductiveTypeReferersUpToDepth

-- 依存関係のマップを名前でソートする機能
inductive SortReferees : Type where
| mk : SortReferees

-- 依存関係のマップを依存関係の長さでソートする機能
inductive SortRefereesByDepLength : Type where
| mk : SortRefereesByDepLength

-- 要件
inductive Requirement : Type where
| mk
(getInductiveTypeDeps : GetInductiveTypeDeps)
(getReferees : GetReferees)
(getInductiveTypeReferersUpToDepth : GetInductiveTypeReferersUpToDepth)
(sortReferees : SortReferees)
(sortRefereesByDepLength: SortRefereesByDepLength)
: Requirement

-- 計画
inductive Plan : Type where
  | initial (requirement : Requirement) : Plan

-- 目的
inductive Purpose : Type where
| mk : Purpose

-- 目標
inductive Goal : Type where
| mk
(plan : Plan)
(purpose : Purpose)
: Goal


#eval show MetaM Unit from do
  let refereesMap ← getReferees `Goal 3
  for (name, deps) in refereesMap.toList do
    IO.println s!"{name}: {deps}"
