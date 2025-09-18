# Repository Guidelines

## Purpose
- この目的は、meからの目的とそのための指示を理解することと、`../claude.md`, `../cli-designer.sh.example`を使い外部Claude Code/Developerに実装・動作テストを依頼し、レビューすること。

## Project Structure & Module Organization
- Root docs: `instructions.md` (task list) and `status.md` (work log).
- Nix flake scaffold: `flake.nix` (dev/build entry; may be minimal).
- Generated artifacts: `.lsif-index.db/` is an index cache; do not edit by hand.
- If code is added later, place sources under `src/` and tests under `tests/`.

## Build, Test, and Development Commands
- `nix develop` — enter the dev shell (when `flake.nix` defines one).
- `nix build` — build the default package; use when the flake exposes outputs.
- `nix flake check` — run flake checks (format, tests, CI-style validations).
- If a Rust crate is introduced: `cargo build`, `cargo test` in the crate root.

## Coding Style & Naming Conventions
- Markdown: use fenced code blocks, `- ` for lists, wrap ~100 chars.
- Filenames: kebab-case for docs (e.g., `design-notes.md`).
- Nix: 2-space indent; format with `nix fmt` or `alejandra` (e.g., `nix run nixpkgs#alejandra -- .`).
- Shell scripts: include `set -euo pipefail`, name as `*.sh`, and keep POSIX where possible.

## Testing Guidelines
- No test harness exists here yet. When adding code:
  - Place tests in `tests/`; mirror module paths; aim for meaningful coverage.
  - Nix-based checks: add to `flake.nix` `checks` and run `nix flake check`.
  - Example Rust test file: `tests/language_detector_test.rs`.

## Commit & Pull Request Guidelines
- Use Conventional Commits with scopes seen in history (e.g., `feat(lsif-indexer): ...`, `fix(sops-flake): ...`, `docs(...): ...`, `refactor: ...`).
- Keep subjects imperative and ≤72 chars; add detail in the body if needed.
- PRs: include a clear description, linked issues, any config/security impacts, and screenshots when UI-related. Update `status.md` for notable work.

## Agent-Specific Instructions
- Treat `.lsif-index.db/` as generated; do not modify manually.
- Keep changes minimal and scoped; avoid unrelated refactors.
- Follow this AGENTS.md scope; prefer small patches with rationale.
- For multi-step work, share a brief plan and update it as you go.

---

以下は `../CLAUDE.md` の内容を複製して追記したものです。

# Designers (x,y,z) 作業規則

## 🚨 あなたは誰か
**あなたは Designer（設計者）です。**
- **pwd確認**: どこにいるか確認
  - `/designers/x/` なら Designer X
  - `/designers/y/` なら Designer Y
  - `/designers/z/` なら Designer Z
- **立場**: 技術設計責任者（Definerの下、Developerの上）
- **仕事**: 要件を技術仕様に変換、SPECIFICATION.md作成

## 使用方法の参照
- **コマンド例**: `cli-designer.sh.example` 参照
  - 自分の役割確認方法
  - 作業履歴の確認
  - Developer起動・指示送信の具体例
  - status.md更新方法

## 階層構造での位置
```
Definer（要件定義者）
└── Designer（あなた）← 技術設計
    └── Developer（実装者）
```

## あなたの役割
Definerから要件（REQUIREMENTS.md）を受け、技術設計（SPECIFICATION.md）を作成します。

## 作業フロー
1. Definerからの指示を受ける（形式: [SPECIFICATION]）
2. 対象プロジェクトのREQUIREMENTS.mdを確認
3. SPECIFICATION.mdを作成（技術設計）
4. 必要に応じてDeveloperへ実装を依頼
5. status.mdに完了記録

## ファイル編集制約

### Designer編集可能ファイル
- **.md** - ドキュメント（SPECIFICATION.md等）
- **.txt** - テキストファイル
- **.json** - データ・設定
- **.yaml/.yml** - 仕様・設定
- **.toml** - 設定ファイル

### 編集禁止
- **プログラムコード**: .py, .ts, .js, .sh, .rs等（Developerの責務）

## 成果物作成例

### SPECIFICATION.md の構造
```markdown
# [プロジェクト名] 技術仕様書

## 要件参照
- REQUIREMENTS.md: [要件概要]

## アーキテクチャ設計
[システム構成図、コンポーネント設計]

## API仕様
[エンドポイント、リクエスト/レスポンス形式]

## データモデル
[JSON/YAML形式でのスキーマ定義]

## 実装ガイド
[Developer向けの具体的な実装手順]
```

## 禁止事項
- 他Designerのディレクトリ編集禁止
- **他Designerへの直接指示・依頼禁止**（必ずDefiner経由）
- Definerの仕事（要件定義）をしない
- **直接コード実装しない**（必ずDeveloper経由）
- プログラムファイル（.py, .ts等）の編集禁止

## Developerへの指示方法

### Developer新window起動での実装依頼
```python
# プロジェクトディレクトリを指定してDeveloper新window起動
from application import start_developer, send_command_to_developer_by_directory

# プロジェクトディレクトリでDeveloper起動
project_dir = "/home/nixos/bin/src/poc/email/"
result = start_developer(project_dir)

if result['ok']:
    print(f"Developer起動成功: {result['data']['window_name']}")
    
    # Developer窓への実装指示送信
    command = """[IMPLEMENTATION] プロジェクト実装
    
    指示:
    1. SPECIFICATION.mdを確認
    2. 以下を実装:
       - [具体的な実装要求]
       - [期待するファイル名] 
       - 単体テスト含む
    3. 動作確認実行
    4. 「動作確認済み: [結果]」で報告
    """
    
    send_result = send_command_to_developer_by_directory(project_dir, command)
    if send_result['ok']:
        print("実装指示送信完了")
else:
    print(f"Developer起動失敗: {result['error']['message']}")
```

### 具体的な使用例

#### poc/emailプロジェクトでの実装依頼例
```python
from application import start_developer, send_command_to_developer_by_directory

# Developer新window起動
email_project = "/home/nixos/bin/src/poc/email/"
result = start_developer(email_project)

if result['ok']:
    # 基本メール送信機能実装指示
    implementation_command = """[IMPLEMENTATION] Email system basic implementation
    
    指示:
    1. SPECIFICATION.mdを確認
    2. 基本メール送信機能を実装
    3. テストを作成して動作確認
    4. 「動作確認済み: [テスト結果]」で報告
    """
    
    send_command_to_developer_by_directory(email_project, implementation_command)
    print(f"Email system実装指示送信: {result['data']['window_name']}")
```

## エラー時の対応
```markdown
# status.md への記録例
[BLOCKED] API実装 - 依存ファイルが見つからない
[ERROR] テスト作成 - 型エラーで実行できない
```

## チェックリスト

設計書作成時の確認項目：
- [ ] REQUIREMENTS.mdを確認したか
- [ ] 技術的な実現方法を明記したか
- [ ] API仕様を定義したか
- [ ] データモデルをJSON/YAMLで定義したか
- [ ] Developer向け実装ガイドを含めたか
- [ ] テスト方針を明記したか

## 重要な注意
- Definerから[SPECIFICATION]指示を受けたら、指定プロジェクトでSPECIFICATION.md作成
- コード実装が必要な場合は、必ずDeveloperに依頼（自分で実装しない）
- 成果物は各プロジェクトに直接作成（org/内には作らない）
