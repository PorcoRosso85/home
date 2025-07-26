# kuzu_py - KuzuDB Thin Wrapper for Nix

## 概要

KuzuDBのNixパッケージを提供し、薄いヘルパー関数でin-memory/persistence切り替えを簡単にします。

### 設計原則
- **薄いラッパー**: KuzuDBのAPIを隠さず、最小限のヘルパー関数のみ提供
- **規約準拠**: エラー処理、ロギング、モジュール設計の規約に従う
- **インフラ層のみ**: ビジネスロジックなし、技術的な実装のみ

### 実現した要件

#### 1. Nix環境でのKuzuDB提供
**要件**: `python312Packages.kuzu`をflakeで提供する
**実現**: 
- `persistence/flake.nix`でNixパッケージのkuzuを設定
- PyPIではなくNixpkgsのkuzuを使用
- カスタマイズ可能な`customKuzu`として定義

#### 2. 最小限の動作テスト
**要件**: in-memory動作テストの作成
**実現**: `test_minimal_kuzu.py`で3つのテスト実装
- Kuzuインポートテスト
- In-memoryデータベース基本動作（CREATE NODE、クエリ実行）
- persistenceモジュール統合テスト

#### 3. PyPI依存の削除
**要件**: `pyproject.toml`からkuzuだけを削除
**実現**: 
- 親ディレクトリの`pyproject.toml`からkuzu依存を削除
- Nix環境でのみkuzuを提供する構成に移行

#### 4. 外部からのPythonライブラリ参照
**要件**: 
- storeに入れずにURI指定だけで参照可能に
- カスタマイズしたkuzuだけを参照したい
**実現**:
- flakeの`lib.pythonPath`出力でモジュールパスを公開
- `PYTHONPATH`環境変数による直接参照を実現
- Nixパッケージ化は不要、ファイルシステム上のパスを直接使用

#### 5. 呼び出し側サンプル
**要件**: `poc/libflake/python/`に使用例を作成
**実現**:
```nix
# flake.nix
inputs.persistence.url = "path:../../../persistence";
shellHook = ''
  export PYTHONPATH="${persistence.lib.pythonPath}:$PYTHONPATH"
'';
```
```python
# main.py
from core.database import create_database, create_connection
```

## 技術的な課題と解決

### 名前衝突問題
**問題**: ローカルの`kuzu/`ディレクトリとNixパッケージの`kuzu`が衝突
**解決経緯**:
1. 初期: `kuzu/` → インポート時に衝突
2. 第1次対応: `persistence_kuzu/` → 長い名前
3. 最終: `kuzu_py/` → シンプルで明確

### Nixストアの制約
**問題**: Nixは**Gitに追跡されているファイルのみ**をストアにコピー
**影響**: ディレクトリ名変更後も`git add`するまで反映されない
**教訓**: 開発中は頻繁な`git add`が必要

## 現在の構成

```
persistence/
├── flake.nix          # メインflake、lib.pythonPath = ./kuzu_py
├── kuzu_py/
│   ├── flake.nix      # 最小構成（将来の拡張用）
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       └── database.py # KuzuDBファクトリー実装
└── test_minimal_kuzu.py
```

## 使用方法

### 1. 外部プロジェクトから参照
```nix
{
  inputs.persistence.url = "path:/path/to/persistence";
  
  # shellHookで
  export PYTHONPATH="${persistence.lib.pythonPath}:$PYTHONPATH"
}
```

### 2. Pythonコードでのインポート
```python
# KuzuDBのAPIを直接使用
from kuzu_py import Database, Connection

# またはヘルパー関数を使用
from kuzu_py import create_database, create_connection

# In-memoryデータベース（Result型で安全）
db_result = create_database(":memory:")
if "error" not in db_result:
    conn_result = create_connection(db_result)
```

### 3. 開発環境
```bash
nix develop
```

## 特徴

- **Nixパッケージ化不要**: PYTHONPATHによる直接参照
- **カスタマイズ可能**: `customKuzu`でNixレベルのカスタマイズ
- **PyPI非依存**: Nixpkgsのkuzuのみ使用
- **シンプル**: 最小限の構成で外部参照を実現

## 提供する機能

### ヘルパー関数
- `create_database(path)`: DatabaseResult型を返す安全なDB作成
- `create_connection(db)`: ConnectionResult型を返す安全な接続作成

### Result型
- エラー処理は例外ではなくResult型で実装
- `DatabaseResult = Union[kuzu.Database, ErrorDict]`
- `ConnectionResult = Union[kuzu.Connection, ErrorDict]`

## クエリローダー機能（実験的）

### 概要
開発の便宜性向上のため、`.cypher`ファイルからCypherクエリを読み込む機能を追加しています。

**注意**: この機能は実験的な追加であり、将来的に別パッケージへ分離される可能性があります。

### 設計の背景
- **利便性**: 長いCypherクエリをファイルとして管理することで、可読性とメンテナンス性を向上
- **開発効率**: クエリの再利用とバージョン管理を容易に
- **責務の明確化**: コアの責務は「KuzuDBの薄いラッパー」のまま維持

### 機能
- `.cypher`ファイルからクエリテキストを読み込み
- ファイルパスによるクエリ管理
- エラーハンドリングはResult型で統一

### 今後の方針
この機能は以下の理由により、将来的に分離される可能性があります：
- コアの責務（薄いKuzuDBラッパー）から逸脱
- 独立したユーティリティとしての価値
- 異なる使用パターンや要件への対応

現時点では開発の利便性を優先して同梱していますが、本パッケージの主要な責務は「Nix環境でのKuzuDB提供」と「最小限のヘルパー関数」であることに変わりありません。