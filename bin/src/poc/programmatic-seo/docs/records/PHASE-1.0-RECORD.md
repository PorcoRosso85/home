DELETE AFTER PROJECT HANDOFF IF REDUNDANT WITH TAG NOTES

**背景**
- コアrepoは巨大、fixブランチに他作業が並行コミットされる前提で進行。
- 現状はPhase 1.1まで実装済み（ゼロCFのsitemap.xml/hreflang生成を追加）。DoV/flake checks/生成物/受領票で緑を確認済み。
  - 受領票: `docs/.receipts/1.1.done:1`
  - ステータス: `docs/PHASES_STATUS.json:1`（1.1=completed）
- 履歴確認（読み取りのみのgitで特定）
  - Phase 1.1導入コミット: `5bfe1bd9` feat: implement Phase 1.1 "Lite+pSEO" programmatic SEO system
    - 追加: `scripts/build-sitemap.ts:1`, `scripts/build-hreflang.ts:1`, `docs/testing/phase-1.1.md:1`
    - `flake.nix:1` に apps/checks（sitemap/hreflang）を追加
  - Phase 1.0最終Fix: `b3be2559` fix: complete Phase 1.0 programmatic SEO foundation fixes
  - Phase 1.0実装: `d9d4418d` feat: implement complete Programmatic SEO Phase 1.0 foundation

**Phase 1.0 を記録する理由・目的・要件**
- 理由/目的
  - 既知良品(1.1)の完全性を担保しつつ、fixブランチを1.0相当に限定リバートできるようにする。
  - 巨大repo/並行開発下でも、回帰時に迅速に再現・復旧できる根拠（証跡）を残す。
  - 将来の1.0切り出し（独立flake）や1.2移行に備え、状態の境界を明確化。
- 要件（監査可能・低リスク）
  - 実行ログと数値指標を残す（Exit 0、URL件数/先頭loc、ESM/IIFEサイズ、HEAD/clean）。
  - ロック/ツールチェーンは固定（`--no-write-lock-file`徹底、`flake.lock`不更新）。
  - 型/ビルド/生成物のDoVで緑（`nix run .#check|.#build-*`、`nix flake check`）。
  - リバートは1.1特有差分のみをパス限定・段階実行（可逆・最小衝突）。
  - 生成物は追跡しない前提（必要な固定は受領票・ログ・タグで担保）。

**検討している戦略**
- 採用方針（低コスト・低リスク）
  1) 1.1担保のプリフライト実行と記録
     - `nix run --no-write-lock-file .#check`
     - `nix run --no-write-lock-file .#build-snippet`
     - `nix run --no-write-lock-file .#build-sitemap`
     - `nix run --no-write-lock-file .#build-hreflang`
     - `nix flake check --no-write-lock-file`
     - 記録: `docs/verification-log-1.1.md:1` にExit 0/指標/HEAD/clean/受領票抜粋を追記
  2) 1.1の凍結（推奨: タグ）
     - 例: `git tag -a phase-1.1-freeze -m "freeze 1.1 @ <HEAD>"` → `git tag -l | grep phase-1.1-freeze`
  3) 1.1差分の限定リバート計画を明文化
     - 対象をパスで列挙し、`docs/revert-plan-1.1.md:1` に記録
       - 生成: `scripts/build-sitemap.ts:1`, `scripts/build-hreflang.ts:1`
       - 検証: `scripts/validate-sitemap.js:1`, `scripts/validate-hreflang.js:1`（存在する場合）
       - flake: `flake.nix:1` の1.1追加 apps/checks（sitemap/hreflang）
       - docs: `docs/testing/phase-1.1.md:1`, `docs/.receipts/1.1.done:1`, `docs/PHASES_STATUS.json:1` の1.1更新
       - 生成物: `public/sitemap.xml:1`, `public/hreflang.html:1`, `public/hreflang.json:1`, `public/hreflang.xml:1`（追跡していれば）
  4) 限定リバートの段階実行（コミット単位×パス限定）
     - 例: `git revert -n 5bfe1bd9 -- scripts/build-sitemap.ts scripts/build-hreflang.ts flake.nix docs/testing/phase-1.1.md`
     - 段階ごとに競合解消→`git commit`、`git status`=cleanを確認
  5) Phase 1.0受入確認（DoV）
     - `nix run --no-write-lock-file .#check` / `.#build-snippet`
     - `nix flake check --no-write-lock-file`（1.1検証は消失していること）
     - `nix run .#serve-examples`
     - 記録: `docs/verification-log-1.0.md:1` を作成
  6) 完了と整合性チェック
     - `git status` clean、タグ参照OK、fixブランチで1.0のみ動作、並行コミット影響なしを確認
     - `docs/phase-separation-completed.md:1` に完了レポートを記録

- 代替案の比較（参考）
  - worktree＋sparse（最も安全・推奨）: 物理分離で干渉ゼロ。ただし今回は「fixブランチ内で完結」方針のため採用見送り。
  - ディレクトリ・スナップショット: `snapshots/phase-1.1/` に証跡/生成物のみ保管（ソースは避ける）。タグの方が軽量・正確。

**備考**
- すべての実行は `--no-write-lock-file` を付け、`flake.lock`の更新を避ける。
- `tsconfig.json:1` や `packages/**` は仕様変更しない（fixブランチの並行作業と矛盾させない）。
- 生成物は原則追跡しない。固定が必要ならタグ/ログ/受領票で担保する。

**署名/日付**
- Prepared by: Phase Separation Ops (assistant)
- Date: 2025-09-29 (ISO 8601)
- Related tag (予定/実績): `phase-1.1-freeze`
