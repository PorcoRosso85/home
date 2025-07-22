# エントリーポイント規約

## プロジェクトタイプ別の構成

### ライブラリプロジェクト
| レイヤー | ファイル | 責務 |
|:--|:--|:--|
| Flake | `flake.nix` | パッケージ定義、開発環境 |
| Library | `mod.{ext}` | 公開API、型定義 |

### CLIプロジェクト
| レイヤー | ファイル | 責務 |
|:--|:--|:--|
| Flake | `flake.nix` | アプリ定義（default, test, readme） |
| Library | `mod.{ext}` | コア機能の公開API |
| CLI | `main.{ext}` | I/O制御、mod.{ext}の呼び出し |

## Flakeの必須要素

### 共通（ライブラリ・CLI両方）
- `packages.default`: メインパッケージ
- `devShells.default`: 開発環境
- `apps.test`: テスト実行

### CLI専用
- `apps.default`: 利用可能コマンド一覧（BuildTime評価）
- `apps.readme`: README.md表示

## 関連規約
- [nix_flake.md](./nix_flake.md) - Flakeレイヤーの詳細
- [module_design.md](./module_design.md) - ライブラリ設計