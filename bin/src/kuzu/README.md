# Kuzu 

Kuzuグラフデータベースを用いた関数型設計ツール

## 概要

このパッケージは、Kuzuグラフデータベースを利用して関数型設計を管理するツールです。SHACL制約を用いてデータの整合性を保証し、Function.Meta.jsonフォーマットによる関数定義の追加と管理を行います。

## 実行方法

### 環境変数の設定と実行
必要なライブラリパスを設定して実行するには、以下のコマンドを使用します：

```bash
# Pythonバージョン確認
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python --version

# コマンドの基本形式
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert
```

### upsertコマンドの基本例

```bash
# コマンドヘルプの表示
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert --help
```

### upsertコマンドの使用方法

コマンドヘルプを表示するには以下のコマンドを実行してください：

```bash
# コマンドヘルプの表示
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python /home/nixos/bin/src/kuzu/upsert/__main__.py --help
```

使用可能なコマンドの詳細については、上記のヘルプコマンドを参照してください。

### browseモジュールの実行方法

browseモジュールは、Kuzuグラフデータベースの内容をブラウザで表示するためのDenoベースのアプリケーションです。

**重要: browseモジュールは必ず `/home/nixos/bin/src/kuzu/browse` ディレクトリ内で実行してください。**

```bash
# 基本的な実行方法
cd /home/nixos/bin/src/kuzu/browse
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run -A build.ts

# Cypherクエリファイルをマウントする実行方法 (推奨)
cd /home/nixos/bin/src/kuzu/browse
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run -A build.ts \
  --mount /home/nixos/bin/src/kuzu/query/ddl:/ddl:*.cypher \
  --mount /home/nixos/bin/src/kuzu/query/dml:/dml:*.cypher \
  --mount /home/nixos/bin/src/kuzu/query/dql:/dql:*.cypher

# アクセス
# http://localhost:5173/
```

**注意**: 
- browseモジュールを他のディレクトリから実行すると、Viteが src/kuzu/ 以下の React 依存ファイルも読み込んでしまい、エラーが発生します。これはViteがプロジェクト構造を検出する仕組みによるものです。
- エラー「ディレクトリ dql の読み込みに失敗しました」を防ぐため、DDL、DML、DQLの3つのディレクトリを全てマウントすることをお勧めします。

browseモジュールの詳細な使用方法については、`browse/CONVENTION.md`を参照してください。

## 機能

- Kuzuグラフデータベースによる関数型情報の保存と管理
- SHACL制約による関数型メタデータの検証
- JSONフォーマットによる関数型定義の追加
- 関数型一覧の表示と詳細情報の取得
- ブラウザでのデータ可視化と対話的操作（browseモジュール）

## 要件

- Python 3.11以上（upsertモジュール用）
- Kuzu 0.9.0以上
- PyShacl 0.30.1以上（upsertモジュール用）
- RDFLib 7.1.4以上（upsertモジュール用）
- Pytest 8.3.5以上（テスト実行用）
- Deno 1.37以上（browseモジュール用）

## パッケージ構造

- `upsert/`: upsertモジュール（関数型定義の追加・更新）
  - `__main__.py`: エントリーポイント
  - `interface/cli.py`: CLIインターフェース
  - `application/`: アプリケーション層
  - `domain/`: ドメイン層
  - `infrastructure/`: インフラ層
  - `design_shapes.ttl`: SHACL制約定義ファイル
  - `example_function.json`: サンプル関数型定義
  - `.venv`: 仮想環境ディレクトリ
- `query/`: queryモジュール（クエリの管理）
  - `dml/`: DMLクエリファイル
  - `call_dml.py`: Cypherクエリローダー（DML・DDL対応）
  - `init/`: 初期化データディレクトリ（CONVENTION.yaml等）
- `browse/`: browseモジュール（データのブラウザ表示）
  - `build.ts`: Denoビルドスクリプト
  - `deno.json`: Deno設定ファイル
  - `src/`: ソースコードディレクトリ
  - `public/`: 静的ファイルディレクトリ
- `db/`: データベースディレクトリ（初期化時に作成）


## テスト実行

テストを実行するには、以下のコマンドを使用します：

```bash
# call_dmlモジュールのテスト実行
/home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m pytest ../query/call_dml.py
```
