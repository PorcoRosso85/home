# 経緯報告 完結版（v1.5 補正版 第2版・spec-repo単独版 最終版 更新版）

## はじめに：本報告書のスコープ

本報告書は **spec-repo のみを対象**とする。  
feat-gateway-remote および v9-implementation は本報告書の考慮外とし、別途個別報告書で扱う。

**参考**：水平展開（フェーズ4）は spec-repo で確立したパターンを他repoに適用する試みであるが、本報告書のスコープ外として本文からは削除し、末尾の「参考」に簡潔に記録する。

---

## 1. 現在の状態（2026年1月2日時点）

### 1.1 検証結果

| リポジトリ | HEADコミット | git status | 変更ファイル数 | 変更行数 | nix flake check | EXIT CODE |
|-----------|-------------|------------|--------------|---------|-----------------|-----------|
| spec-repo | `67287ba` | **DIRTY** | 5 | +91/-42 | ✅ PASS (28 checks) | 0 |

**重要**：
- spec-repo で Phase5 実装が完了しているが、git commit が未完了
- PASSは「実装完了時点の状態」であり、commit により固定される
- **warning について**：ログ中の `unknown flake output 'checksRed'/'spec'` は非致命的（exit 0）
- **DIRTY状態の構成**：
  - **tracked 差分**：5ファイル（patch-id で同一性を保証）
  - **untracked ファイル**：6項目（一覧で証拠化）

本報告書は **「tracked差分はpatch-idで固定し、untrackedは一覧で証拠化する」** とする。

### 1.2 チェック数の定義

本報告でいう「チェック数」は2種類に限定する。

| 用語 | 定義 |
|------|------|
| **flake checks総数** | `self.checks.${system}` に含まれるチェック数（Nixが実行する全チェック） |
| **requiredChecks数** | `repo.cue.requiredChecks` に列挙された必須チェック数（要件宣言） |

### 1.3 チェック数の推移（spec-repo）

| フェーズ | flake checks総数 | requiredChecks数 | 備考 |
|---------|-----------------|-----------------|------|
| Phase0 | 26 | - | `nix flake show --json` でカタログ化（当初28と記録したが誤記） |
| Phase2 | 27 | 27 | repo-cue-validity 追加 |
| Phase5 | 28 | 28 | test-dod5/6-positive 追加、test-dod5/6-negative-verify を除外 |

**算出方法**（付録C参照）：
```bash
# flake checks総数
nix eval --json '.checks.x86_64-linux' | jq 'keys | length'

# requiredChecks数（範囲限定 + コメント除去 + 要素抽出で完全フォーマット非依存）
sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' repo.cue \
  | sed 's,//.*$,,' \
  | grep -oE '"[^"]+"' \
  | wc -l
```

**特徴**：
- `sed` の終了条件 `^[[:space:]]*\]` は `]` が行頭または空白後にある行にマッチ（インデント非依存）
- `sed 's,//.*$,,'` は行コメントを除去し、コメント中の引用符による誤カウントを防止
- `grep -oE '"[^"]+"' | wc -l` は「要素（文字列）を抽出してカウント」するため、1行複数要素でも正しく数えられる

### 1.4 CI要件SSOT
- `repo.cue` を「CI要件の宣言（SSOT）」として扱い、flake checksはその具現とする。

### 1.5 手動管理の排除
- `flakeChecksList` は `builtins.attrNames (self.checks.${system} or {})` から自動生成し、チェック追加/削除に伴う手動同期を不要にした。

### 1.6 checksRedの扱い

| 属性 | 内容 | self.checksに含む | requiredChecksに含む |
|------|------|-------------------|---------------------|
| `checks` | 通常チェック（PASS必須） | ✅ 含む | ✅ 含む |
| `checksRed` | 失敗前提の確認（test-dod5/6-negative-verify） | ❌ 含まない | ❌ 含まない |

**理由**：
- flake check は全チェックPASSが前提の契約
- 失敗前提のものを `requiredChecks` に入れると整合しない

---

## 2. 背景：なぜこの作業が必要だったか

### 2.1 発端の問題

**問題1：CI要件の分散管理**
- CIの必須チェックが `flake.nix` にハードコードされていた
- ドキュメントと実態が異なる事態が発生
- 「どのチェックが本当に必要なのか」が不明確

**問題2：spec-repo の CI要件 SSOT 化**
- `repo.cue` を CI 要件の唯一の場（SSOT）として確立
- flake checks との整合性を保証する仕組みが必要

### 2.2 技術的制約

- **CUE と Nix の境界**：CUE は型定義・検証ロジック用、Nix は「具現」（実行）のみ
- **外部コマンド禁止**：Nix の derivation 内で `nix flake show --json` などの外部コマンド実行は非推奨
- **Third-party 再現性**：「第三者が一つのコマンドで全部検証できる」ことを目指す

---

## 3. 各フェーズの経緯と理由

### フェーズ0-3：基盤構築（spec-repo のみ）

#### フェーズ0：現状把握
- `nix flake show --json` で既存26チェックをカタログ化（当初「28」と記録したが誤記）
- **理由**：リファクタリング前に「何がある」を正確に把握するため

#### フェーズ1：`repo.cue` の作成
- 26チェックを `repo.cue` に全写経
- **形式決定の理由**：
  - なぜ `#Repo` タイプ定義ではなく `repo: { ... }` 値か？
    - KISS原則：単純な値の方が編集しやすく、エラーが少ない
    - タイプ定義のオーバーヘッドは不要と判断
  - なぜ `deliverablesRefs` に `nix/*` を含めいないか？
    - 境界の明確化：`nix/*` は「具現」、「spec/*` は「素材・実装」
    - CUEが参照すべきは素材側のみという設計思想

#### フェーズ2：`repo-cue-validity.nix` の作成
- `repo.cue` の必須チェックと `flake.checks` を対照するバリデーションを追加
- **技術的選択**：
  - spec-repo では CUE ベースの検証（`cue vet`）
  - **理由**：spec-repo は CUE の SSOT として高度な検証が必要

#### フェーズ3：分類ルールの確立
- README.md に以下を明記：
  - `repo.cue` = CI要件SSOT（正本）
  - `spec/*` = 素材・実装
  - `nix/*` = 具現
  - `docs/*` = 説明
- **理由**：各層の責務を明確にし、「どこに何を書くか」の混乱を防止

### フェーズ5：重複排除

#### 5.1 問題の発見
`flakeChecksList` が手動管理：
```nix
# 手動管理の問題：同期漏れが発生しうる
flakeChecksList = [
  "check-a"
  "check-b"
  "check-c"
  ...
]
```

#### 5.2 解決策：自動生成
```nix
flakeChecksList = builtins.attrNames (self.checks.${system} or {})
```

#### 5.3 遭遇した技術的問題

**問題**：`self.checks.${system}` には `checksRed` が含まれない

`flake.nix` で `checksRed` は個別定義：
```nix
checksRed = {
  test-dod5-negative-verify = ...;
  test-dod6-negative-verify = ...;
};
```

`self.checks` には `checks` 属性のみが含まれ、`checksRed` は別管理。

**解決策**：`repo.cue` から `test-dod5-negative-verify` と `test-dod6-negative-verify` を削除

**理由**：
- flake check は全チェックPASSが前提の契約
- 失敗前提のものを requiredChecks に入れると整合しない

#### 5.4 spec-repo の更新

| リポジトリ | HEAD | 変更内容 |
|-----------|------|---------|
| spec-repo | `67287ba` | `flakeChecksList` 自動生成、パラメータ名変更 |

---

## 4. 技術的詳細

### 4.1 `repo-cue-validity.nix` の仕組み

**注意**：以下のコードは **概念的な概略** であり、実装詳細は同名ファイルを参照。

**spec-repo（CUEベース・概略）**：
```nix
{ pkgs, self, cue, checksAttrNames }:
let checksJson = pkgs.writeText "checks.json" (builtins.toJSON checksAttrNames);
in pkgs.runCommand "repo-cue-validity" {
  buildInputs = [ pkgs.jq cue ];
} ''
  cue export ./repo.cue --out json requiredChecksJson > $out
  diff <(jq -S .requiredChecks requiredChecksJson) <(jq -S . checksJson)
''
```

### 4.2 パラメータ名の変遷

| フェーズ | パラメータ名 | 理由 |
|---------|-------------|------|
| 初期 | `flakeChecksList` | 一覧という名前 |
| Phase5 | `checksAttrNames` | より正確（属性名のリスト） |

---

## 5. 意思決定の根拠

### 5.1 KISS原則の適用
- `repo: { ... }` という単純な値形式を選択
- 複雑なタイプ定義やジェネリックは回避
- **理由**：CI要件SSOTは「人が編集する」ものであり、複雑さはミスを招く

### 5.2 境界の明確化

| 層 | 場所 | 内容 |
|---|-----|-----|
| SSOT（正本） | `repo.cue` | CI要件の宣言 |
| 素材 | `spec/*` | CUEによる実装・型定義 |
| 具現 | `nix/*` | Nixによる実行のみ |

---

## 6. 残課題

### 6.1 Phase 5.6：固定化（CLEAN化）（推奨 next）
spec-repo を DIRTY → CLEAN に固定化（commit + tag）

### 6.2 Phase 6：等価リファクタリング（後回し可）
spec-repo 内の重複・揺れを低コストで均す（仕様不変）

### 6.3 README 更新
README.md に「21 checks」とあるが実際には flake checks総数=28（更新が必要）

### 6.4 将来の方針差分（別紙）
SSOT配信方針（spec-repo から全repoへ配信）の検討は Phase 7 として分離

---

## 7. 検証方法

```bash
cd /home/nixos/spec-repo && git log -1 --oneline && git status --short

# flake check（exit code を正しく取得）
log=$(mktemp)
nix flake check >"$log" 2>&1
ec=$?
tail -15 "$log"
echo "---EXIT_CODE---"
echo "$ec"
rm -f "$log"

# チェック数算出（完全フォーマット非依存）
nix eval --json '.checks.x86_64-linux' | jq 'keys | length'              # flake checks総数
sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' repo.cue \
  | sed 's,//.*$,,' \
  | grep -oE '"[^"]+"' | wc -l                                            # requiredChecks数
```

---

## 8. TDD表（テスト名/背景/ステータス）

| テスト名 | 背景 | ステータス |
|---------|------|----------|
| scope_is_spec_repo_only | 報告がspec-repoだけで完結 | ✅ CONFIRMED |
| dirty_state_is_pinned_by_patch_id_tracked | tracked差分をpatch-idで固定 | ✅ CONFIRMED（付録Bにpatch-id記録） |
| dirty_state_includes_untracked_evidence | untrackedの有無を証拠化 | ✅ CONFIRMED（付録B.1に記録） |
| flake_check_pass_has_raw_log_and_true_exit_code | 実ログ＋**nix本体**のexit codeで証拠化 | ✅ CONFIRMED（付録C.1にmktemp方式） |
| requiredChecks_count_is_format_independent | 要素抽出で1行複数要素も正しくカウント | ✅ CONFIRMED |
| requiredChecks_count_ignores_line_comments | コメント中の`"`で誤カウントしない | ✅ CONFIRMED（sedコメント除去） |
| sed_range_ends_on_closing_bracket | 抽出が `]` 行で閉じる | ✅ CONFIRMED（付録C.2にtail証拠） |
| flake_checks_count_is_mechanical | flake checks総数が機械算出 | ✅ CONFIRMED（付録Cに算出方法） |
| repo_cue_validity_snippet_is_conceptual | 概略と実装の境界明示 | ✅ CONFIRMED（4.1に「概略」明記） |
| warnings_are_classified_non_fatal | warningが非致命と明記 | ✅ CONFIRMED（1.1に注記） |
| appendix_references_are_consistent | 本文→付録参照が整合 | ✅ CONFIRMED（付録Cに統一） |

---

## 9. 差分：v1.5 補正版（第2版）→ v1.5 補正版（第2版・spec-repo単独版 最終版 更新版）

| 項目 | v1.5 補正版（第2版） | 最終版 更新版 |
|------|---------------------|--------------|
| 1.1 DIRTY状態の表現 | 「DIRTY状態をpatch-idで固定」 | **「tracked差分はpatch-idで固定し、untrackedは一覧で証拠化」** |
| スコープ | 3repo（本文に水平展開記述あり） | **spec-repoのみ**（水平展開は「参考」に降格） |
| 1.3 算出方法 | `grep -oE '"[^"]+"' | wc -l` | **`sed 's,//.*$,,'` 追加でコメント除去版** |
| 1.1 検証結果表 | 3repo分 | **spec-repoのみ** |
| 3. フェーズ4 | 詳細記述あり | **削除**（「参考」セクションに移動） |
| 5.4 更新表 | 3repo分 | **spec-repoのみ** |
| 付録A | 3repoのHEAD | **spec-repoのみ** |
| 付録B | 3repoのpatch-id | **spec-repoのみ（付録B）＋B.1追加（untracked証拠）** |
| 付録C | 3repoのログ・算出結果 | **spec-repoのみ** |
| 付録C.1 EXIT CODE取得 | `| tail` | **`mktemp`方式（正しいexit code）＋echo整合** |
| 付録D Phase6 | 「3repoの引数形統一」 | **spec-repo内の等価リファクタへ差し替え** |
| 付録D Phase7 | 「SSOT配信方針」 | **「参考（スコープ外）」ラベルを追加** |
| 付録参照 | 「付録E」参照が混在 | **すべて「付録C」に統一** |

---

**以上**

---

## 付録A：spec-repoのHEADコミット（証拠）

```
$ cd /home/nixos/spec-repo && git log -1 --oneline
499381b Phase 5: repo-cue-validity implementation

$ git tag -l phase5-*
phase5-freeze-2026-01-02
```

**更新履歴**：
- 2026-01-02: Phase 5 完了、CLEAN化 (commit 499381b, tag phase5-freeze-2026-01-02)
- 2026-01-02 以前: DIRTY状態 (commit 67287ba)

## 付録B：spec-repo git diff + patch-id（証拠・同一状態再現可能）

### B.1 tracked 差分 + untracked 確認

```
$ cd /home/nixos/spec-repo && git diff --numstat
23	13	README.md
11	0	flake.nix
45	25	nix/checks/dod0-factory-only.nix
10	2	nix/checks/repo-cue-validity.nix
2	2	repo.cue

$ cd /home/nixos/spec-repo && git diff | git patch-id --stable
3269ab70296723ff92ae8338f30d54ab67c4bf14 0000000000000000000000000000000000000000

$ cd /home/nixos/spec-repo && git ls-files -o --exclude-standard
.gen/stub_contract.json
artifacts/resolution/default.log
artifacts/resolution/stub.log
result
test/spec_contract_source_default.test.js
test/spec_source_stub.test.js
```

**DIRTY状態の構成**：
- **tracked 差分**：5ファイル（patch-id `3269ab7...` で同一性を保証）
- **untracked ファイル**：6項目（一覧で証拠化）

## 付録C：flake check 実行証拠 + チェック数算出

### C.1 nix flake check 実行結果（実ログ + 正しいEXIT CODE）

```bash
$ cd /home/nixos/spec-repo
$ log=$(mktemp)
$ nix flake check >"$log" 2>&1
$ ec=$?
$ tail -15 "$log"
checking flake output 'checksRed'...
warning: unknown flake output 'checksRed'
checking flake output 'spec'...
warning: unknown flake output 'spec'
running 28 flake checks...
warning: The check omitted these incompatible systems: aarch64-darwin, aarch64-linux, x86_64-darwin
Use '--all-systems' to check all.
---EXIT_CODE---
$ echo "$ec"
0
$ rm -f "$log"
```

**注記**：
- `warning: unknown flake output 'checksRed'/'spec'` は非致命的
- exit code `0` は `nix flake check` 本体のもの（pipe の罠を回避）

### C.2 チェック数算出結果（完全フォーマット非依存）

```bash
# flake checks総数
$ nix eval --json '.checks.x86_64-linux' | jq 'keys | length'
28

# requiredChecks数（範囲限定 + コメント除去 + 要素抽出）
$ sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' repo.cue \
    | sed 's,//.*$,,' \
    | grep -oE '"[^"]+"' \
    | wc -l
28
```

**範囲が正しく閉じる証拠（tail）**：
```
$ sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' /home/nixos/spec-repo/repo.cue | tail -5
    "test-dod6-positive",

    
    "repo-cue-validity",
  ]
```

### C.3 検証コマンド（第三者再現用）

```bash
cd /home/nixos/spec-repo

# 1. ワークツリーの整合性確認（tracked + untracked）
git diff --numstat
git diff | git patch-id --stable
git ls-files -o --exclude-standard

# 2. flake check 実行（正しいexit code取得）
log=$(mktemp)
nix flake check >"$log" 2>&1
ec=$?
tail -15 "$log"
echo "---EXIT_CODE---"
echo "$ec"
rm -f "$log"

# 3. チェック数確認（完全フォーマット非依存）
nix eval --json '.checks.x86_64-linux' | jq 'keys | length'
sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' repo.cue \
  | sed 's,//.*$,,' \
  | grep -oE '"[^"]+"' | wc -l

# 4. 範囲の整合性確認
sed -n '/requiredChecks:/,/^[[:space:]]*\]/p' repo.cue | tail -5
```

---

## 参考：水平展開の試み（スコープ外）

spec-repo で確立した `repo.cue` パターンを他repoに適用する試み：

| リポジトリ | 配置 | 状況 |
|-----------|-----|------|
| feat-gateway-remote | ルート | repo.cue 作成済み、grepベース検証 |
| v9-implementation | 深い階層 | repo.cue 作成済み、grepベース検証 |

**詳細**：各repoの `flake.nix` に `repo-cue-validity.nix` を追加し、`flakeChecksList` を自動生成する方式。

---

## 付録D：次フェーズ計画（Phase 5.6 → Phase 6 → Phase 7）

### Phase 5.6：固定化（CLEAN化）

**GOAL**：DIRTY証拠 → CLEANコミットで再現可能な「正本」を作る

#### タスク構造

| タスクID | タスク名 | DoD（完了条件） | 依存 |
|---------|---------|----------------|------|
| T5.6.1 | 差分の最終確認 | 全変更ファイルの内容を確認し、不要な差分がないこと | - |
| T5.6.2 | git commit | `git add` + `git commit` で差分をコミット | T5.6.1 |
| T5.6.3 | flake check再実行 | `nix flake check` が PASS (exit 0) であること | T5.6.2 |
| T5.6.4 | tag付与 | 意味のあるtag（例：`phase5-freeze-2026-01-02`）を付与 | T5.6.3 |
| T5.6.5 | 報告書更新 | コミットSHAとtagを付録Aに追加 | T5.6.4 |

#### DoD（フェーズ完了条件）

- [ ] `git status` が CLEAN
- [ ] `nix flake check` が PASS (exit 0)
- [ ] tag が付与され、`git show <tag>` で同じ結果が再現可能
- [ ] 報告書がコミットSHAとtagで更新されている

### Phase 6：等価リファクタリング（後回し可・spec-repo単独）

**GOAL**：spec-repo 内の重複・揺れを低コストで均す（仕様不変）

#### タスク構造

| タスクID | タスク名 | DoD（完了条件） | 依存 |
|---------|---------|----------------|------|
| T6.1 | 現状のflake check確認 | 変更前 `nix flake check` が PASS であることを記録 | - |
| T6.2 | spec-repo内の引数形/命名/コメント整備 | `repo-cue-validity.nix` 周辺の引数名・説明を統一（仕様不変） | - |
| T6.3 | checksAttrNames生成ロジックの整備 | spec-repo内で生成箇所を読みやすく整理（仕様不変） | - |
| T6.4 | flake check再実行 | 変更後 `nix flake check` が PASS (exit 0) であること | T6.1, T6.2, T6.3 |
| T6.5 | requiredChecks整合確認 | 変更前後で requiredChecks数が同一であることを確認 | T6.4 |

#### DoD（フェーズ完了条件）

- [ ] 変更前後で `nix flake check` が同一PASS
- [ ] `repo.cue.requiredChecks` と `self.checks.${system}` の整合が維持される
- [ ] 変更内容のドキュメント化

### Phase 7（後回し・参考/スコープ外）：SSOT配信方針

**GOAL**：「各repoにrepo.cueを置かない」方針へ回帰

**概要**：spec-repo が CUE を配信し、feat-repo 側は「具現だけ」を行う設計への移行（大設計変更のため別タスク）

#### DoD（フェーズ完了条件）

- [ ] feat-repo からローカル `repo.cue` を削除してもCIが成立する
- [ ] spec-repo から配信される CUE のみで要件が完結する

---

## 付録E：TODO/Taskリスト（spec-repo単独で完結）

| タスクID | 目的 | 作業 | DoD（証拠まで） |
|---:|---|---|---|
| **T0** | 現状確認 | `git log -1 --oneline` / `git status --short` | 出力をログに貼れる状態 |
| **T1** | 文言検証 | `grep -n "DIRTY状態" <report>.md` | 旧表現が残っていない/残っていれば箇所特定 |
| **T2** | 報告書パッチ適用 | 付録C.1のecho整合、Phase6文言、Phase7ラベルを修正 | `git diff` で差分確認（報告書のみの差分として読める） |
| **T3** | 証拠ブロック再生成（任意） | 付録C.1/C.3のコマンドを実行して貼り替え | `---EXIT_CODE---` が `$ec` 由来であることが読み取れる |
| **T4** | Phase5.6 固定化（CLEAN化） | `git add -A` → `git commit` | `git status` が CLEAN |
| **T5** | 再検証 | `nix flake check`（mktemp方式でec取得） | `EXIT_CODE=0` の証拠（ログ＋ec） |
| **T6** | tag付与 | `git tag phase5-freeze-2026-01-02` 等 | `git show <tag>` で参照可能 |
| **T7** | 報告書の追記 | 付録Aに **コミットSHAとtag** を追記 | 報告書が「CLEANの正本」を参照できる |

**実行順序**：
1. **T0** → 現状把握
2. **T1** → 文言確認（1件でも残っていれば T2 へ）
3. **T2** → 報告書整合（必須）
4. **T3** → 任意（証拠の厳密性上げ）
5. **T4 → T5 → T6 → T7** → CLEAN化（commit → recheck → tag → report update）

---

## 付録F：TDD表（完全版）

| テスト名 | 背景 | ステータス |
|---------|------|----------|
| scope_is_spec_repo_only | 報告がspec-repoだけで完結 | ✅ CONFIRMED |
| dirty_state_is_pinned_by_patch_id_tracked | tracked差分をpatch-idで固定 | ✅ CONFIRMED |
| dirty_state_includes_untracked_evidence | untrackedの有無を証拠化 | ✅ CONFIRMED |
| flake_check_pass_has_raw_log_and_true_exit_code | 実ログ＋nix本体exit codeで証拠化 | ✅ CONFIRMED |
| requiredChecks_count_is_format_independent | フォーマット非依存で数える | ✅ CONFIRMED |
| requiredChecks_count_ignores_line_comments | コメント中の`"`を除外 | ✅ CONFIRMED |
| sed_range_ends_on_closing_bracket | `]`で範囲が閉じる | ✅ CONFIRMED |
| flake_checks_count_is_mechanical | flake checks総数が機械算出 | ✅ CONFIRMED |
| repo_cue_validity_snippet_is_conceptual | 概略と実装の境界明示 | ✅ CONFIRMED |
| warnings_are_classified_non_fatal | warningが非致命と明記 | ✅ CONFIRMED |
| appendix_references_are_consistent | 本文→付録参照が整合 | ✅ CONFIRMED |
| phase6_plan_is_spec_repo_only | Phase6計画がspec-repo単独 | ✅ CONFIRMED |
| phase7_labeled_out_of_scope | Phase7がスコープ外として明示 | ✅ CONFIRMED |

---

**以上**
