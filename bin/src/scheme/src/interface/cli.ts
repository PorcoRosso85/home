#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run

/**
 * メタスキーマ管理CLI
 * 
 * 分割されたモジュール構造を採用し、各機能を適切なファイルに分離しています。
 * 
 * - cli/cliController.ts: コマンド実行を制御するコントローラー
 * - cli/cliUtils.ts: ヘルプ表示やディレクトリ確認などのユーティリティ
 * - cli/requirementsCommands.ts: 統一要件関連のコマンド
 * - cli/typeGenerationCommands.ts: 型生成関連のコマンド
 */

import { IntegratedCliController } from "./cli/cliController.ts";

/**
 * CLIのエントリポイント
 */
if (import.meta.main) {
  const controller = new IntegratedCliController();
  await controller.main();
}
