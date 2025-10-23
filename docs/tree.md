# Repository Tree (Latest Design Only)
> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

---

## 実装順（フェーズと最小到達点）

### P0（必須・最小で動く状態）
1. **SSOTを先に作る**（最小1エントリ）
   - `contracts/ssot/_toc.yaml`（id↔パス索引；仮でOK）
   - `contracts/ssot/_config.cue`（基本設定）
   - 例：`contracts/ssot/ugc/post@1.2.0/contract.cue`（schema最小＋stories≥3）
2. **index生成**
   - `tools/generator`：SSOT → `capsules/index.cue`（決定的生成）
   - `.gitignore`：`capsules/index.cue` を除外
   - Gate：**直import禁止**（indexのみ参照）
3. **薄いmanifest**
   - `features/**/manifest.cue`：`contractRef` のみ
   - `deployables/**/manifest.cue`：`import "capsules/index"` + `uses[]`
   - Gate：**存在チェック**（`uses[]` が index にあるか）
4. **gen 最小**
   - `tools/generator gen run/check`：`gen/tests|seeds|docs/**` 生成
   - **fingerprint一致**でCI Fail（手書き混入防止）
5. **CI直列**
   - `build(index) → cue vet → gen run → gen check → gates(min) → runner(min)`
   - runner最小：`pytest -m "smoke or unit"` / `go test`
6. **ポリシー最小**
   - `.pre-commit-config.yaml`：`cue fmt` / 直import禁止
   - `CODEOWNERS`：大束で開始（後で細分化）

### P1（堅牢化）
7. **determinism**
   - `jq -S`/`yq`でキー順固定・時刻/TZ/乱数除去
   - Gate：決定性チェック
8. **plan-diff強化 / changed-only**
   - 依存DAG差分（孤児/未提供/循環）→ Fail
   - 変更パスだけ実行（paths-filter）
9. **PII / golden-ttl**
   - `tools/mask`（PII検出・マスク）
   - ゴールデンの期限チェック

### P2（外部公開・スケール）
10. **dist（需要が出たら）**
    - `dist/contracts/{openapi,asyncapi,schema}/...` を**CIアーティファクトのみ**出力
    - Gate：`parity(index↔dist)`（逆投影/同値）
11. **シャーディング（閾値超えたら）**
    - index が重くなったら A–M/N–Z 分割→上位で合成
12. **ドキュ整備（必要になったら）**
    - Redoc/Pages公開、`contracts/reports/**` 可視化

---

## PoC/実験（下書き不要運用）
- `sandbox/**`（または `_poc/**`）配下に自由に作成可。**manifestが無い限り**スキャン対象外。
- **依存禁止**：indexに無いIDへの `uses[]` はFail。
- **TTLレポート**：長期放置は警告。昇格は「薄いmanifest追加 → SSOT登録 → index反映」。

---

## 最新ツリー（役割コメント＋フェーズ）

```
repo/
├─ contracts/                                   # 契約ドメインの集約 [P0]
│  └─ ssot/                                     # ★契約本文（人が編集）[P0]
│     ├─ _toc.yaml                              # id↔パス索引 [P0]
│     ├─ _config.cue                            # 生成/ゲートの設定 [P0]
│     ├─ ugc/
│     │  └─ post@1.2.0/{contract.cue,stories/**,seeds/**}   # 最小1件から [P0]
│     ├─ seo/...
│     └─ media/...
├─ capsules/                                    # ★内部インデックス（生成・非コミット）[P0]
│  └─ index.cue                                 # import先（唯一の参照点）[P0]
├─ features/                                    # 提供側（薄いmanifestのみ）[P0]
│  ├─ ugc/post/
│  │  ├─ manifest.cue                           # { contractRef }（schemaはSSOT）[P0]
│  │  └─ gen/{tests,seeds,docs}/**              # 生成物（fingerprint一致）[P0]
│  └─ ...
├─ deployables/                                 # 依存側（薄いmanifest）[P0]
│  ├─ api/public/
│  │  ├─ manifest.cue                           # import "capsules/index" + uses[] [P0]
│  │  └─ gen/{tests,seeds,docs}/**              # 生成物（fingerprint一致）[P0]
│  └─ ...
├─ sandbox/                                     # ★PoC/実験（manifestが無い限り完全除外）[随時]
│  └─ feature-x/…
├─ tools/                                       # 実行物の集約 [P0→P1]
│  ├─ generator/**                              # SSOT→index/gen/(opt:dist) [P0]
│  ├─ gates/**                                  # 直import/存在→determinism/plan-diff/PII [P0→P1]
│  ├─ runners/{python,go}/**                    # pytest/go test ラッパ [P0]
│  └─ mask/**                                   # PIIマスク/正規化 [P1]
├─ policy/                                      # 規約（宣言）[P1]
│  └─ cue/
│     ├─ vocab/{caps,errors,ratelimit}.cue      # 語彙 [P1]
│     └─ rules/{strict,determinism,contract-diff,...}.cue    # ルール [P1]
├─ dist/                                        # 外部配布（原則アーティファクト）[P2]
│  └─ contracts/{openapi,asyncapi,schema}/**
├─ ci/                                          # CI周辺 [P0→P1]
│  ├─ config/{phases.yaml,pipeline.yaml}        # 実行順/Fail条件 [P0]
│  ├─ reports/**                                # gates出力（diff/parity 等）[P1→P2]
│  └─ artifacts/**                              # 中間成果物 [P0]
├─ env/                                         # 環境テンプレ [P1]
│  └─ templates/{dev,stg,prod}.env
├─ .github/workflows/{ci.yml,nightly.yml,quarantine.yml}      # 直列パイプライン [P0]
├─ CODEOWNERS                                   # 大束で開始→細分化 [P0→P1]
├─ .pre-commit-config.yaml                      # cue fmt / 直import禁止 / secrets [P0]
├─ .gitignore                                   # capsules/index.cue, gen/** を除外 [P0]
└─ docs/
   ├─ adr/adr-0.10.8.md                         # 本ADR（final表記なし）[P0]
   └─ tree.md                                   # ←このファイル [P0]
```

---

必要なら、PoC TTLレポート用の最小スクリプト雛形と、paths-filter を使った changed-only CI例もすぐ出します。

---

## ADR 0.10.10版ツリー（Flake駆動マニフェスト）

> 凡例: ★=必須、◇=生成(非コミット推奨)、△=任意

```
repo/
├─ flake.nix                               △  ルート開発環境/DevShell等（任意）
├─ flake.lock                              △
├─ .gitignore                              ★  capsules/index.cue, gen/**, .artifacts/** を除外
├─ .editorconfig                           △
├─ .pre-commit-config.yaml                 △  cue fmt / secrets 等
├─ Makefile                                △  `make ci-local` など
├─ CODEOWNERS                              △
├─ README.md                               △
├─ docs/
│  ├─ adr/
│  │  ├─ adr-0.10.8.md                     △  既存
│  │  └─ adr-0.10.10.md                    ★  改善版ADR
│  └─ tree.md                              △  最新ツリー説明（本ファイル）
├─ contracts/
│  └─ ssot/                                ★  仕様本文（人が編集）
│     ├─ _toc.yaml                         ★  契約ID↔パス索引
│     ├─ _config.cue                       ★  生成/ゲート設定
│     ├─ ugc/
│     │  └─ post@1.2.0/
│     │     ├─ contract.cue                ★  schema/caps/errors/rateLimit 等
│     │     ├─ stories/                    ★  正常/失敗/境界 ≥3
│     │     │  ├─ normal.cue
│     │     │  ├─ error.cue
│     │     │  └─ boundary.cue
│     │     └─ seeds/                      △
│     │        └─ post.json
│     └─ ...（他ドメイン）
├─ features/
│  └─ <domain>/<feature>/                  ★  1機能=1フレーク
│     ├─ flake.nix                         ★  meta.manifest.kind="feature", contractRef, owner, stability...
│     ├─ meta/                             ★  （旧 cue.README/）
│     │  ├─ impl.resp.cue                  ★  役割/可視性/allowedImports=["capsules/index"]
│     │  └─ modules.resp.cue               △  modules 共通規約
│     ├─ modules/                          △  多言語実装（manifestは増やさない）
│     │  ├─ go-api/
│     │  │  ├─ go.mod / main.go / ...
│     │  │  └─ module.resp.cue             ★  intents.provides 等（薄く）
│     │  ├─ py-jobs/
│     │  │  ├─ pyproject.toml / jobs/**
│     │  │  └─ module.resp.cue             ★
│     │  └─ ts-sdk/
│     │     ├─ package.json / src/**
│     │     └─ module.resp.cue             ★
│     └─ gen/                              ◇  tests/seeds/docs（指紋一致）
│        ├─ tests/{unit,integration,e2e,uat}/**
│        ├─ seeds/**
│        └─ docs/**
├─ deployables/
│  └─ <tier>/<name>/                       ★  1デプロイ=1フレーク
│     ├─ flake.nix                         ★  meta.manifest.kind="deployable", uses=[...], owner...
│     ├─ meta/
│     │  ├─ service.resp.cue               ★  ポート/SLO/公開範囲
│     │  └─ deps.resp.cue                  ★  uses と parity 検証（flakeと部分集合一致）
│     ├─ modules/
│     │  ├─ go-service/
│     │  │  ├─ main.go / ...
│     │  │  └─ module.resp.cue             ★  intents.uses ⊆ flake.uses
│     │  ├─ py-migrations/
│     │  │  ├─ scripts/**
│     │  │  └─ module.resp.cue             ★
│     │  └─ ts-proxy/
│     │     ├─ src/**
│     │     └─ module.resp.cue             ★
│     └─ gen/                              ◇
│        ├─ tests/**
│        └─ docs/**
├─ capsules/                               ◇  生成（非コミット）
│  └─ index.cue
├─ .artifacts/                             ◇  非コミット生成物の集約
│  ├─ manifests/
│  │  ├─ features/<domain>/<feature>/manifest.cue
│  │  └─ deployables/<tier>/<name>/manifest.cue
│  └─ reports/
│     ├─ parity.json
│     ├─ plan-diff.json
│     ├─ contract-diff.json
│     ├─ determinism.json
│     ├─ license.csv
│     └─ dag.dot / dag.png
├─ tools/
│  ├─ bridge/
│  │  └─ flake2manifest                    ★  flake→manifest.cue（決定的・非コミット）
│  ├─ generator/
│  │  ├─ gen                               ★  SSOT→gen/dist
│  │  └─ check                             ★  指紋検証
│  ├─ gates/                               ★  失敗で止める
│  │  ├─ parity.cue                        # modules ⊆ flake（uses/provides）
│  │  ├─ plan-diff.cue                     # 孤児/未提供/循環
│  │  ├─ contract-diff.cue                 # SemVer破壊
│  │  ├─ cap-dup.cue                       # 提供ID重複
│  │  ├─ determinism.cue                   # 決定性
│  │  ├─ mask.cue                          # PII
│  │  ├─ license.cue                       # ライセンス
│  │  └─ cve.cue                           # CVE
│  ├─ runners/
│  │  ├─ python/runner.sh                  ★  タグ実行（unit/smoke等）
│  │  └─ go/runner.sh                      ★
│  ├─ graph/
│  │  └─ build-graph.sh                    △  契約DAG可視化
│  └─ paths-filter/
│     └─ filters.yml                       △  changed-only 実行
├─ policy/
│  └─ cue/
│     ├─ schemas/
│     │  ├─ manifest.cue                   ★  厳格スキーマ（未知キー禁止）
│     │  ├─ module.cue                     ★
│     │  └─ responsibility.cue             ★
│     └─ rules/
│        ├─ strict.cue                     ★  直import禁止 等
│        ├─ determinism.cue                ★
│        ├─ contract-diff.cue              ★
│        ├─ plan-diff.cue                  ★
│        ├─ cap-dup.cue                    ★
│        ├─ parity.cue                     ★
│        ├─ mask.cue                       ★
│        ├─ license.cue                    ★
│        └─ cve.cue                        ★
├─ dist/                                   △  リリース時のみ固定化
│  └─ contracts/{openapi,asyncapi,schema}/**
├─ sandbox/                                △  PoC（TTL警告・スキャン除外）
│  └─ feature-x/
└─ .github/
   ├─ workflows/
   │  ├─ ci.yml                            ★  直列: index→flake2manifest→vet→gen→gates→runners→graph→paths-filter
   │  ├─ nightly.yml                       △
   │  └─ quarantine.yml                    △
   ├─ PULL_REQUEST_TEMPLATE.md             △  互換性/PII/SLO チェック欄
   └─ ISSUE_TEMPLATE/{bug_report.md,feature_request.md}  △
```

### 使い方の要点（0.10.10版）

**人が編集**:
- `contracts/ssot/**`
- `features/**/flake.nix`
- `deployables/**/flake.nix`
- 各 `*.resp.cue`

**自動生成**:
- `capsules/index.cue`
- `.artifacts/manifests/**`
- `features|deployables/**/gen/**`

**検証**:
- CIの`gates/*`で parity / plan-diff / contract-diff / determinism / PII / license / CVE をFail化

### フェーズ実装チェックリスト（0.10.10版）

#### P0で必須
- [ ] `bridge/flake2manifest`
- [ ] `gates/parity|strict`
- [ ] `capsules/index.cue` 生成
- [ ] `runners` 最小

#### P1で必須
- [ ] `policy/cue/schemas/{manifest,module,responsibility}.cue`
- [ ] `gates/{determinism,plan-diff,cap-dup}`

#### P2で必須
- [ ] `tools/{graph,paths-filter}`
- [ ] `gates/{license,cve}`
- [ ] `dist/` 方針

---

## ADR 0.10.11版ツリー（consumes採用 / Secrets必須 / SBOM & CVE）

<!-- 責務: リポジトリ全体の構成と各アイテムの役割を一覧で示す最新ツリー -->

```
repo/
├─ docs/
│  └─ adr/
│     ├─ adr-0.10.8.md                          # 旧ADR（参照）
│     ├─ adr-0.10.10.md                         # Flake駆動マニフェスト
│     └─ adr-0.10.11.md                         # 最新ADR（consumes/Secrets/SBOM/CVE）
├─ contracts/
│  └─ ssot/                                      # 契約のSSOT（人が編集）
│     ├─ _toc.yaml                               # 契約ID↔パス索引
│     ├─ _config.cue                             # 生成/ゲート設定
│     └─ <domain>/<subject>@<semver>/            # 各契約
│        ├─ contract.cue                         # 契約スキーマ/制約
│        ├─ stories/{normal,error,boundary}.cue  # 受入シナリオ
│        └─ seeds/*.json                         # サンプルデータ（任意）
├─ features/
│  └─ <domain>/<feature>/
│     ├─ flake.nix                               # feature宣言（contractRef等）
│     ├─ meta/
│     │  ├─ impl.resp.cue                        # 責務（可視性/所有者/allowedImports）
│     │  └─ modules.resp.cue                     # モジュール規約（任意）
│     └─ modules/<lang>-<role>/
│        └─ module.resp.cue                      # 実装の意図（必要最小のconsumes）
├─ deployables/
│  └─ <tier>/<name>/
│     ├─ flake.nix                               # deployable宣言（consumes/owner等）
│     ├─ meta/
│     │  ├─ service.resp.cue                     # SLO等
│     │  └─ deps.resp.cue                        # consumes集約（任意）
│     └─ modules/<lang>-<role>/
│        └─ module.resp.cue                      # 実装のconsumes（宣言の部分集合）
├─ policy/
│  └─ cue/
│     ├─ config.cue                              # ポリシーフラグ（fail/warn/off）
│     ├─ schemas/
│     │  ├─ manifest.cue                         # manifest厳格スキーマ
│     │  ├─ module.cue                           # module厳格スキーマ
│     │  └─ responsibility.cue                   # responsibility厳格スキーマ
│     └─ rules/
│        ├─ strict.cue                           # 直import禁止等
│        ├─ parity.cue                           # 宣言↔実装の部分集合検証
│        ├─ determinism.cue                      # 決定性チェック
│        ├─ secrets.cue                          # Secrets検出（必須）
│        ├─ license.cue                          # ライセンスチェック
│        └─ cve.cue                              # CVE突合
├─ tools/
│  ├─ bridge/
│  │  └─ flake2manifest                          # flake→manifest.cue決定的生成
│  ├─ generator/
│  │  ├─ gen                                     # SSOT生成
│  │  └─ check                                   # 指紋検証
│  ├─ security/
│  │  ├─ sbom.sh                                 # SBOM生成
│  │  └─ cve_scan.sh                             # CVE突合
│  ├─ gates/
│  │  └─ *.cue                                   # ルール実行エントリ
│  ├─ paths-filter/
│  │  └─ filters.yml                             # 変更→再実行対象の最小ルール
│  └─ graph/
│     └─ build-graph.sh                          # 契約DAG可視化（任意）
├─ capsules/
│  └─ index.cue                                  # SSOT→索引（生成・非コミット）
├─ .artifacts/
│  ├─ manifests/                                 # 生成されたmanifest.cue（非コミット）
│  └─ reports/
│     ├─ summary.json                            # 監査サマリ
│     ├─ sbom.json                               # SBOM（リリース時）
│     ├─ cve.json                                # CVE（週次+リリース前）
│     ├─ parity.json                             # パリティ検証結果
│     └─ secrets.json                            # Secrets検出結果
├─ .github/
│  └─ workflows/
│     └─ ci.yml                                  # 直列CI（SBOM=release/CVE=weekly）
└─ .gitignore                                    # capsules/, .artifacts/ 除外
```

### Contract ↔ Capability 関係性（0.10.11版）

**1つの contract** = **複数の capability**

```
contract: ugc/post@1.2.0
  ├─ capability: ugc.post.create
  ├─ capability: ugc.post.read
  ├─ capability: ugc.post.update
  └─ capability: ugc.post.delete
```

- **所有権**: capability は contract に一意に紐づく
- **バージョン**: capability 自体はsemverを持たない（破壊的変更はcontractのsemverで管理）
- **依存**: deployable は capability ID を `consumes` する

### 主要変更点（0.10.11版）

1. **`uses` → `consumes`**: 依存の表現を統一（`uses`はdeprecated）
2. **Secrets検出必須**: 高エントロピー・鍵・トークン検出でFail
3. **SBOM生成**: リリース時に依存台帳を自動生成
4. **CVE突合**: 週次+リリース前に既知脆弱性をチェック
5. **監査サマリ**: `.artifacts/reports/summary.json` に集約

### 用語の変更（0.10.11版）

- ❌ **uses** → ✅ **consumes** (deployable/moduleの依存宣言)
- ✅ **provides** (featureの提供、contractRefから派生)
- ✅ **capability** (契約が提供する個別機能ID: `domain.subject.verb`)
