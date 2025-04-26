# Upsert

Kuzuグラフデータベースを用いた関数型設計ツール

## 概要

このパッケージは、Kuzuグラフデータベースを利用して関数型設計を管理するツールです。SHACL制約を用いてデータの整合性を保証し、Function.Meta.jsonフォーマットによる関数定義の追加と管理を行います。

## 実行方法

### 環境変数の設定と実行
必要なライブラリパスを設定して実行するには、以下のコマンドを使用します：

```bash
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert
```

### コマンドの例

```bash
# データベース初期化
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert --init

# サンプル関数を追加
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert --add example_function.json

# 登録された関数の一覧表示
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert --list

# 特定の関数の詳細表示
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH /home/nixos/bin/src/kuzu/upsert/.venv/bin/python -m upsert --get MapFunction
```

## 機能

- Kuzuグラフデータベースによる関数情報の保存と管理
- SHACL制約による関数メタデータの検証
- JSONフォーマットによる関数定義の追加
- 関数一覧の表示と詳細情報の取得

## 要件

- Python 3.11以上
- Kuzu 0.9.0以上
- PyShacl 0.30.1以上
- RDFLib 7.1.4以上
- Pytest 8.3.5以上（テスト実行用）

## パッケージ構造

- `__main__.py`: エントリーポイント
- `interface/cli.py`: CLIインターフェース
- `application/`: アプリケーション層
- `domain/`: ドメイン層
- `infrastructure/`: インフラ層
- `design_shapes.ttl`: SHACL制約定義ファイル
- `example_function.json`: サンプル関数定義
- `.venv`: 仮想環境ディレクトリ
- `db`: データベースディレクトリ（初期化時に作成）
