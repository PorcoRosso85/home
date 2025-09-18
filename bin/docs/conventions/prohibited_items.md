# 禁止事項

クリーンで予測可能なコードベースを維持するため、以下の項目を禁止します。
これらの多くは、Linterによって自動的に検出・警告されるべきです。

## 全言語共通

- **例外の投げ上げ**: `throw`, `raise`, `panic` など、エラーハンドリングの規約に反する例外の使用。
- **グローバル変数の書き換え**: アプリケーションのどこからでも変更可能なグローバル状態の作成。
- **`TODO`/`FIXME`コメント**: タスク管理はIssueトラッカーで行うべきです。コード内に未完了のタスクを示すコメントを残してはいけません。
- **ダミー実装・モック**: 本番コード内に、テスト用のダミー実装やモックを含めること。
- **クラスベースOOP**: [設計原則](./design_principles.md) に従い、データと振る舞いを分離した関数型スタイルを優先します。
- **シェルベースの独自実装**: flake.nix内でのシェルスクリプトによる機能実装。必要な機能は適切なNixパッケージまたはflake inputとして実装すること。
- **print文の使用**: Pythonでの`print()`使用。構造化ログ出力には`bin/src/telemetry/*/log_py`を使用すること。
- **`nix-shell`の使用**: レガシーな`nix-shell`コマンドやshebangの使用。代わりに`nix shell`を使用すること（[nix_flake.md](./nix_flake.md)参照）。

## 言語別

| 言語 | 禁止事項 |
| :--- | :--- |
| **TypeScript** | `any` 型の使用, `@ts-ignore` コメント, `interface` の使用 (`type` を使用), CommonJS (`require`/`module.exports`) |
| **Python** | `"type: ignore"` コメント, `import *`, Pythonファイル間の直接import（flake.nix経由のモジュール化を使用すること） |
| **Go** | `main` パッケージ以外での `panic` の使用, 複雑な `init` 関数 |
| **Rust** | 本番コードでの `.unwrap()` や `.expect()` の使用, 過剰な `unsafe` ブロック |
| **Zig** | デバッグ目的以外での `unreachable` の使用 |
