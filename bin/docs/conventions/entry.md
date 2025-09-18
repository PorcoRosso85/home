# エントリーポイント規約

## 目的

プロジェクトタイプに応じた**エントリーポイントの構造**と**責務分離**を定義する。

## プロジェクトタイプ別の構成

### ライブラリプロジェクト
| レイヤー | ファイル | 責務 |
|:--|:--|:--|
| Flake | `flake.nix` | パッケージング、開発環境の提供 |
| Library | `mod.{ext}` | 公開API、型定義、再利用可能な機能 |

**特徴**: 
- 他のプロジェクトから`import`される前提
- `nix shell`での利用が主体
- 実行可能コマンドは持たない

### CLIプロジェクト
| レイヤー | ファイル | 責務 |
|:--|:--|:--|
| Flake | `flake.nix` | アプリケーション定義、実行環境 |
| Library | `mod.{ext}` | ビジネスロジック、テスト可能なコア |
| CLI | `main.{ext}` | I/O処理、引数解析、mod呼び出し |

**特徴**:
- `nix run`で実行される前提
- LLM-firstな設計（JSON入出力）
- 明確なエントリーポイント

## エントリーポイントの設計原則

### 1. 責務の分離
- **main**: I/O、エラーハンドリング、終了コード管理
- **mod**: ピュアな関数、ビジネスロジック、テスト可能性
- **flake**: パッケージング、依存関係、実行環境

### 2. LLM-first設計
```typescript
// main.ts - I/O層
const input = await readStdin();
const result = processRequest(JSON.parse(input)); // mod.tsの関数
console.log(JSON.stringify(result));
```

### 3. テスタビリティ
- ビジネスロジックは`mod`に集約
- `main`は薄いラッパーとして実装
- 単体テストは`mod`に対して実施

## 必須構成要素

### packages（全プロジェクト）
- `packages.default`: 主要な成果物

### apps（CLIプロジェクト）
- `apps.default`: ヘルプ表示（利用可能コマンド一覧）
- `apps.test`: テスト実行
- `apps.readme`: README表示

### devShells（開発環境）
- `devShells.default`: 開発ツール・環境変数

## 実装の詳細

具体的な実装方法は[nix_flake.md](./nix_flake.md)を参照。

## 関連規約
- [nix_flake.md](./nix_flake.md) - Nix Flakeの実装詳細
- [module_design.md](./module_design.md) - モジュール設計原則
- [testing.md](./testing.md) - テスト戦略