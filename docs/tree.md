# Repository Tree (Latest Design Only)

> 本ファイルは**最新設計のみ**を更新します。ADR本文にはツリーを書きません。

```
repo/
├─ flake.nix                              # 修正済み（ゴミ文字除去）
├─ flake.lock
├─ .gitignore                             # capsules/index.cue, gen/** を除外
├─ docs/
│  ├─ adr/
│  │  └─ adr-0.10.8.md                    # ★最終ADR
│  └─ tree.md                             # ← このファイル
├─ flakes/
│  └─ contracts-index/                    # ★manifest群→capsules/index.cue を決定的生成
│     └─ flake.nix
├─ policy/
│  └─ cue/
│     ├─ schemas/base.cue                 # Closed Schema（未知キー禁止）
│     ├─ strict.cue                       # 直import禁止・既知キー限定
│     ├─ contracts.cue                    # contracts検証ハブ
│     └─ gates/                           # ★品質ゲート群
│        ├─ quality.cue                   # cases≥3, waiver TTL
│        ├─ contract-diff.cue             # SemVer整合
│        ├─ cap-dup.cue                   # capability一意
│        ├─ banned-tags.cue               # 未許可/降格タグ検出
│        ├─ determinism.cue               # UTC/RNG/ID/TZ/順序/JSON正規化
│        ├─ plan-diff.cue                 # 依存・影響差分
│        └─ golden-ttl.cue                # 変動源TTL
├─ tools/
│  ├─ generator/                          # ★manifest→gen/tests|seeds|docs 生成（fingerprint/--check）
│  │  └─ gen
│  ├─ language-packs/
│  │  ├─ python/{templates,steps,runner.sh}
│  │  └─ go/{templates,lib,runner.sh}
│  ├─ gates/
│  │  ├─ export-contracts                 # dist/contracts/** 生成
│  │  └─ gate
│  └─ mask/
│     └─ mask                             # PIIマスク + JSON正規化
├─ features/                              # ★SSOT（人が編集するのはここ）
│  ├─ ugc/post/
│  │  ├─ manifest.cue                     # contract/stories/tags/seed設計図
│  │  ├─ impl/**                          # 実装（任意構成）
│  │  └─ gen/                             # ★生成のみ（手書き禁止）
│  │     ├─ tests/{unit,integration,e2e,uat}/**
│  │     ├─ seeds/**
│  │     └─ docs/**
│  └─ ...（他機能も同様）
├─ deployables/
│  ├─ api/public/
│  │  ├─ manifest.cue                     # Uses列挙（常に import "capsules/index"）
│  │  └─ gen/{tests,seeds,docs}/**
│  └─ ...（web/worker/batch/cron）
├─ capsules/                              # ★生成物（非コミット）
│  └─ index.cue
├─ dist/
│  └─ contracts/**                        # OpenAPI/AsyncAPI/Schema + Auth/RateLimit/Errors（CI出力）
├─ ci/
│  ├─ phases.yaml
│  ├─ pipeline.yaml
│  ├─ reports/**
│  └─ artifacts/**
└─ .github/workflows/
   ├─ ci.yml                               # build→vet→gen→check→gates→runner
   ├─ nightly.yml
   └─ quarantine.yml
```
