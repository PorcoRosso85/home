# AGENTS

本ドキュメントは、Designer/Developer/Definer の役割分担と、`src/poc/sops-flake` を対象にした実運用フロー（`cli-designer.sh.example` に基づく）を明文化します。

## 目的
- 役割と責務の境界を明確化し、作業の手戻りを防止する。
- Designer 主導で Developer を駆動し、成果物・履歴・検証を一貫管理する。
- Claude の起動経路と作業ディレクトリ規約を共有する。

## 役割と責務
- Definer: 要件/方針の定義者。要求の背景・制約・達成条件を示し、[SPECIFICATION] の元ネタ（REQUIREMENTS.md 等）を提供する。
- Designer（あなた）: 仕様策定と実装計画の設計者。`[SPECIFICATION]` を作成し、Developer に `[IMPLEMENTATION]` 指示を出す。進捗の監督・検証・記録を行う。
- Developer: 実装担当。Designer の `[IMPLEMENTATION]` 指示に基づき、コード/テスト/検証を実施し、結果を報告する（例:「動作確認済み: ...」）。

## 対象プロジェクト
- 作業対象: `src/poc/sops-flake`
- 特徴: sops-nix を利用する PoC。依存を pin した再現性の高い環境を前提とする。

## Claude / Developer の起動経路
- 通常、Developer は Claude セッション（`claude-code`）として起動される。
- ランチャー: `src/develop/claude/ui/flake.nix` に定義された flake ベースの CLI（`claude`, `claude-launch`）。
- 起動時の作業ディレクトリ（cwd）: 起動引数で与えたパス、またはカレントディレクトリ。
- 実体の確認例:
  - プロセス: `ps -ef | grep -E 'claude-code|claude-launch' | grep -v grep`
  - 作業ディレクトリ: `for pid in $(pgrep -f 'claude-code'); do ls -l /proc/$pid/cwd; done`

## 運用フロー（Designer 主導）
1) 仕様の参照・策定
- Definer の要件（例: `REQUIREMENTS.md`）を確認し、Designer が `[SPECIFICATION]` を起案。
- 成果物例: `SPECIFICATION.md`, 必要に応じて `VERIFICATION_PLAN.md`。

2) Developer の起動と指示送達
- 参考スクリプト: `src/develop/org/designers/cli-designer.sh.example`
  - 仕様テンプレート生成、履歴の取得、Developer 起動（新ウィンドウ）、`[IMPLEMENTATION]` 指示送付の例を含む。
- 指示タグの使い分け:
  - `[SPECIFICATION]`: 仕様・設計の提示。
  - `[IMPLEMENTATION]`: 実装作業の具体指示（機能、テスト、検証、報告形式を含む）。

3) 進捗・結果の確認
- 履歴参照: `get_claude_history` を用い、`[IMPLEMENTATION]` に対する Developer の報告（例:「動作確認済み: …」）を確認する。
- 結果が未返答の場合は待機/再送を実施する。

4) 記録の更新
- `status.md` に主要イベントを追記（例: 仕様作成完了、実装指示送信、検証完了など）。

5) 再実行/リトライ
- Developer が失敗/未完了の場合、原因の特定と再実行指示（例: `[IMPLEMENTATION] プロジェクト再実行`）。

## 主要ファイルと規約
- `SPECIFICATION.md`: Designer が作成する技術仕様書。実装者向けの API/データモデル/手順/テスト観点を含める。
- `VERIFICATION_PLAN.md`: 検証観点・受入基準・テスト項目の整理（必要に応じて）。
- `status.md`: 日時とイベントを時系列で追記。意思決定や完了報告も記録する。
- `REQUIREMENTS.md`: Definer 提供の要件。変更があれば差分を可視化して追随。

## メッセージ指示テンプレート（例）
- `[SPECIFICATION]` テンプレート要旨
  - 要件参照、アーキテクチャ、API 仕様、データモデル、実装ガイド、検証計画
- `[IMPLEMENTATION]` テンプレート要旨
  - 「仕様参照 → 実装 → テスト → 動作確認報告」の順で実施し、完了時は「動作確認済み: [結果]」と報告

## よくあるフロー（簡易）
1. Designer: `SPECIFICATION.md` を作成/更新
2. Designer: Developer を対象ディレクトリで起動し、`[IMPLEMENTATION]` を送付
3. Developer: 実装/テスト/確認 → 結果報告
4. Designer: 結果確認/差戻し/受入 → `status.md` 更新

## 注意事項 / 前提
- `cli-designer.sh.example` は実行例であり、`application` モジュールの関数（`start_developer` 等）に依存する箇所がある。環境に応じて同等の制御手段（Claude 起動・指示送達）を用意すること。
- `sops-flake` は機密情報の取り扱いを前提とするため、鍵管理・暗号化の取り扱いはリポジトリ内のドキュメント（`poc/sops-flake` 配下の README/USAGE 等）に従うこと。

