# Linter/Formatter

## 方針

コードの品質とスタイルの一貫性は、個人の努力ではなく、ツールによって自動的に強制されるべきです。
すべてのコードは、コミットされる前にLinterとFormatterによるチェックをパスしなければなりません。

## Linter (静的解析ツール)

Linterは、コードの潜在的なバグや、規約違反を検出します。

- **命名規則**: 変数、関数、型などの名前が規約に従っているか。
- **禁止事項の検出**: `any`型、`unwrap()`、`"type: ignore"`など、[禁止事項](./prohibited_items.md)で定められたパターンの使用を検出します。
- **ベストプラクティス**: 各言語のコミュニティで推奨される、より安全で効率的なコードの書き方を強制します。

| 言語 | 推奨Linter |
| :--- | :--- |
| **TypeScript** | ESLint |
| **Python** | Ruff |
| **Go** | Go Linter (`golangci-lint`) |
| **Rust** | Clippy |

## Formatter (コード整形ツール)

Formatterは、インデント、スペース、改行など、コードの見た目を統一します。
これにより、本質的でないスタイルに関するレビューのやり取りをなくします。

| 言語 | 推奨Formatter |
| :--- | :--- |
| **TypeScript** | Prettier |
| **Python** | Ruff Formatter |
| **Go** | `gofmt` |
| **Rust** | `rustfmt` |

## 設定

- プロジェクトのルートディレクトリに、各ツールの設定ファイル（例: `.eslintrc.json`, `pyproject.toml`）を配置します。
- Gitのpre-commitフックなどを利用して、コミット前に自動的にチェックとフォーマットが実行されるように設定することを強く推奨します。
