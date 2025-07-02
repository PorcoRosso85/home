# テスト

## 要求事項

- **公開関数にテスト必須**: `mod.{ext}` からエクスポートされるすべての公開関数は、対応するテストを持つ必要があります。
- **テストファイルの配置**: テストファイルは、テスト対象のファイルと同じディレクトリに配置します。これにより、テスト対象のコードとテストコードが見つけやすくなります。

## ファイル命名規則

| 言語 | ファイル名 |
| :--- | :--- |
| **Python** | `test_<target_file_name>.py` |
| **TypeScript** | `<target_file_name>.test.ts` |
| **Go** | `<target_file_name>_test.go` |
| **Rust** | （同ファイル内に `#[cfg(test)]` ブロックで記述） |
| **Zig** | （同ファイル内に `test "..." { ... }` ブロックで記述） |

## テストランナー

| 言語 | テストランナー |
| :--- | :--- |
| **Python** | `pytest` |
| **TypeScript** | `node:test` または `deno test` |
| **Go** | `go test` |
| **Rust** | `cargo test` |
| **Zig** | `zig test` |

## テスト命名規則

テストケースの名前は、以下の形式で具体的に記述します。

`test_{テスト対象の機能}_{テストの条件}_{期待される結果}`

- **例 (Python)**: `test_calculate_score_with_bonus_returns_correct_sum`
- **例 (TypeScript)**: `test('calculateScore with bonus should return correct sum')`
