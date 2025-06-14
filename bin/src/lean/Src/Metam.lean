import Lean

open Lean Lean.Expr Lean.Meta


-- 1. **# MetaM**: Lean 4のメタプログラミングAPIの中心となる4つのモナド (`CoreM`, `MetaM`, `TermElabM`, `TacticM`) を紹介し、この章で扱う`MetaM`が環境とメタ 変数コンテキストへのアクセスを提供するモナドであることを説明しています。

-- 2. **メタ変数の概要**: メタ変数には「式の中の穴」と「証明目標」という2つの見方があることを説明しています。証明目標の例として `n + m = m + n`、式の穴の例として `Eq.trans` を挙げて、メタ変数の役割を導入しています。

-- 3. **タクティクとメタ変数によるコミュニケーション**: `apply Eq.trans` を例に、タクティクがメタ変数を使ってどのように証明のゴールを操作し、情報を伝達し合うかを解説しています。メタ変数への値の割り当てと、それによるゴールリストの変化を説明しています。

-- 4. **基本的な操作**: `MetaM` モナドで利用できる基本的なメタ変数操作 (`mkFreshExprMVar`: 新しいメタ変数作成, `assign`: 値の割り当て, `getDecl`: 宣言取得, `getType`: 型取得, `instantiateMVars`: メタ変数インスタンス化) を紹介し、コード例を用いて具体的な使い方を示しています。

#eval show MetaM Unit from do
  logInfo "MetaM の例"


#eval show MetaM Unit from do
  -- Nat 型の新しいメタ変数を作成
  let mvar1 ← mkFreshExprMVar (Expr.const `Nat []) (userName := `mvar1)
  let mvar2 ← mkFreshExprMVar (Expr.const `Nat []) (userName := `mvar2)
  let mvar3 ← mkFreshExprMVar (← mkArrow (.const `Nat []) (.const `Nat [])) (userName := `mvar3)

  -- 作成直後のメタ変数は未割り当て
  IO.println s!"meta1: {← instantiateMVars mvar1}" -- meta1: ?_uniq.1

  -- mvar1 に `mvar3 mvar2` を割り当て (mvar1 := mvar3 mvar2)
  mvar1.mvarId!.assign (.app mvar3 mvar2)
  IO.println s!"meta1 割り当て後: {← instantiateMVars mvar1}" -- meta1 割り当て後: ?_uniq.3 ?_uniq.2

  -- mvar2 に `0` を割り当て (mvar2 := 0)
  mvar2.mvarId!.assign (.const `Nat.zero [])
  IO.println s!"mvar2 割り当て後: {← instantiateMVars mvar1}" -- mvar2 割り当て後: ?_uniq.3 Nat.zero

  -- mvar3 に `Nat.succ` を割り当て (mvar3 := Nat.succ)
  mvar3.mvarId!.assign (.const `Nat.succ [])
  IO.println s!"mvar3 割り当て後: {← instantiateMVars mvar1}" -- mvar3 割り当て後: Nat.succ Nat.zero

-- 5. **ローカルコンテキスト**: ローカルコンテキスト (`LocalContext`) の概念、自由変数 (`fvar`) の意味、ローカルコンテキスト取得関数 `getLCtx`、コンテキスト 設定関数 `withContext` の役割を説明しています。例として `myAssumption` タクティクを提示し、`isDefEq` (定義が等しいか判定), `LocalDecl.toExpr` (ローカル変 数を式へ変換) などの関連関数も紹介しています。

-- 6. **遅延代入**: メタ変数の遅延代入という高度な機能に触れ、通常の代入との違いや、関連する関数 (`isAssigned`, `getExprMVarAssignment?`) を使う際の注意点を 簡単に説明しています。

-- 7. **メタ変数の深さ**: メタ変数に深さの概念があること、そして `withNewMCtxDepth` を使うことで一時的なメタ変数を安全に扱う方法について解説しています。

-- 8. **計算**: Leanにおける計算、特に「定義等価性」の概念の重要性を強調しています。異なる式の表現でも、計算結果が同じであれば定義的に等しいとみなされること を説明しています。

-- 9. **完全正規化**: 式を完全正規形にする `reduce` 関数を紹介しています。`#reduce` コマンドとの対応関係や、オプション引数についても触れています。

-- 10. **透明性**: 式の正規化における「透明性モード」 (`reducible`, `instances`, `default`, `all`) の概念を説明しています。透明性モードによって、正規化の際にどこまで定数を展開するかが変わることを解説し、例を用いて各モードの違いを示しています。

-- 11. **弱頭部正規形**: より効率的な正規化形式である弱頭部正規形 (WHNF) と、それを計算する `whnf` 関数を紹介しています。WHNF の例と非 WHNF の例を挙げ、`matchAndReducing` 関数などを例に、タクティク開発における WHNF の重要性を説明しています。

-- 12. **定義等価性判定**: 2つの式が定義的に等しいかを判定する `isDefEq` 関数を紹介しています。`isDefEq` がメタ変数の代入（ユニフィケーション）を行う可能性があること、メタ変数の種類 (`MetavarKind`) が `isDefEq` の挙動に影響を与えることを説明しています。

-- 13. **式の構築 - 関数適用**: `MetaM` での式構築の利点として、暗黙引数や宇宙レベルを自動で推論する `mkAppM` 関数を紹介しています。`mkAppM'` や `mkAppOptM` 関数についても簡単に触れています。

-- 14. **式の構築 - ラムダと全称**: ラムダ抽象や全称量化の式を構築する方法 (`lam`, `forallE`) を説明しています。`withLocalDecl`, `mkLambdaFVars`, `mkForallFVars` などの関数を用いて、より複雑な式を構築するイディオムを示しています。

-- 15. **式の分解**: 式を分解するための関数群、特に `λ` や `∀` バインダーを分解する関数 (`forallTelescope` など) を紹介しています。`myApply` タクティクの例を通して、`forallMetaTelescopeReducing` の使用例を具体的に示しています。

-- 16. **バックトラッキング**: タクティクにおけるバックトラッキングの概念と、`MonadBacktrack` クラス、`saveState`, `restoreState` 関数を紹介しています。`tryM` 関数を例に、状態を保存・復元する方法を示し、`withoutModifyingState`, `observing?` などの便利なコンビネータについても解説しています。また、`try ... catch ... finally` ブロック使用時の注意点も述べています。
