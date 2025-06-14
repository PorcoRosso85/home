# プロジェクト概要

このプロジェクトはPythonを使用して開発されている。

## 開発環境

以下のツールを使用している:

- **Python**: メインのプログラミング言語
- **uv**: パッケージ管理ツール
- **pytest**: テストフレームワーク
- **ruff**: コードのリントとフォーマットツール


以下のファイルがプロジェクトルートに存在することを確認する:
   - `pyproject.toml`
   - `env.sh`
   - `cloudbuild.yaml`

## インストール方法


1. `uv` をパッケージ管理として使用、経緯は下記参照: 

```bash
pip install uv==0.5.14
```

2.  プロジェクトのルートディレクトリで以下のコマンドを実行して、開発に必要なパッケージをインストールする:

仮想環境を構成する

```bash
uv venv
```

運用に必要なパッケージは, pyproject.tomlからインストールする

```bash
uv sync
```

運用に必要なパッケージが別途追加される場合、以下のコマンドを使用するか、pyproject.toml/dependenciesに直接記入する

```bash
uv add [[package_name]]
```

開発のみに必要なパッケージはpyproject.tomlから除外しているため、手動でインストールする

```bash
uv pip install pytest ruff
```

3. プロジェクトメンバーから `env.sh` ファイルを共有してもらい、プロジェクトのルートディレクトリに配置する。このファイルには、アプリケーションおよびコンテナのプッシュに必要な環境変数が格納されている。

```bash
source env.sh
```

4. インストールが完了したら、プロジェクトの開発を開始できる。

## テストの実行

テストを実行するには、以下のコマンドを使用する:

```bash
pytest
```

## コードのリントとフォーマット

コードのリントとフォーマットを行うには、以下のコマンドを使用する:

```bash
ruff check .
ruff format .
```

## コンテナビルドのテスト

コンテナをビルドするには、以下のコマンドを使用する。`env.sh` で設定された環境変数を使用して、プロジェクトのリージョン、ID、コンテナリポジトリ名、イメージ名、およびタグを指定する。

```bash
sudo docker build -t $PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$CONTAINER_REPOSITORY_NAME/$CONTAINER_IMAGE_NAME:$CONTAINER_IMAGE_TAG .
```

このコマンドを実行することで、指定されたタグでコンテナイメージがビルドされ, ビルドが成功したら、以下のコマンドでコンテナを実行してテストできる:

```bash
sudo docker run --rm -p 8080:8080 $PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$CONTAINER_REPOSITORY_NAME/$CONTAINER_IMAGE_NAME:$CONTAINER_IMAGE_TAG
```

このコマンドは、ビルドされたコンテナを実行し、ホストのポート8080をコンテナのポート8080にマッピングする。`--rm` オプションは、コンテナの停止後に自動的にコンテナを削除する。

## Artifact Registry へのアプリケーションのビルドとプッシュ

Artifact Registry にアプリケーションをビルドおよびプッシュするには、以下のコマンドを使用する。このコマンドは、`cloudbuild.yaml` ファイルを使用してビルドプロセスを自動化し、事前に `docker build` コマンドを実行する必要はない。

```bash
gcloud builds submit --config cloudbuild.yaml
```

このコマンドを実行すると、Google Cloud Build が `cloudbuild.yaml` に定義された手順に従ってアプリケーションをビルドし、Artifact Registry にプッシュします。ビルドとプッシュのプロセスが完了すると、指定されたリポジトリにコンテナイメージが保存されます。

## その他

- プロジェクトの詳細な設定や使用方法については、各ツールの公式ドキュメントを参照してください。

- パッケージ管理ツールの選択理由
   - **pip のみの問題**:
     - パッケージ追加時、依存パッケージ `Y` が自動でインストールされるが、削除時に `Y` だけを指定してアンインストールできない。
     - `requirements.txt` にバージョンなしで `X` を記述すると最新版が入り、アプリケーションが不安定になる可能性がある。
     - 開発用ツール（Linter など）の分離管理が難しい。

   - **uv を選んだ理由**:
     - 記述がシンプルで、`lock` ファイルを生成する機能がある。
     - `poetry` や `uv` が候補だったが、直近の評判から `uv` を選択。

   - **目的**:
     - 少数メンバーでの開発環境統一
     - Docker Desktop未使用の環境でも動作
     - 低スペックPCでも動作
     - `devcontainer`ほど重い環境不要


