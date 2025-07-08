#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env --allow-run

/**
 * Gmail CLI エントリポイント
 * 単一のエントリポイントとして、すべての機能を統合
 */

// 実際の実装をインポートして実行
import("./mail/cli_full_auto.ts");