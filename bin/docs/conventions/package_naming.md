# パッケージ命名規約

## 原則

**Hybrid Contextual Naming (HCN) - 文脈を含むハイブリッド命名規約**

```
[<scope>/]<context>-<name>[@<version>]
```

- 内部・外部パッケージ両方に対応する柔軟な命名体系
- 文脈（context）により機能が明確になる命名
- 既存のパッケージマネージャー（npm、Nix等）との互換性

## 命名構造

### 基本構造
- `<context>`: パッケージの分類・用途（database、auth、utils等）
- `<name>`: 具体的な機能名（postgres、jwt、string等）
- `<scope>`: オプショナル。組織・名前空間（@internal、@company等）
- `<version>`: オプショナル。セマンティックバージョニング

### 具体例

```
# 公開パッケージ（スコープなし）
database-postgres
auth-jwt
utils-string

# 内部パッケージ（スコープあり）
@internal/api-gateway
@internal/database-adapter
@company/auth-service
```

## ディレクトリ構造との対応

```
# ディレクトリ → パッケージ名
bin/src/database/postgres/     → database-postgres
bin/src/auth/jwt/             → auth-jwt
bin/src/utils/string/         → utils-string
bin/src/internal/api/gateway/ → @internal/api-gateway
```

### 変換規則
1. 冗長な繰り返しを避ける（utils/string/string → utils-string）
2. 最大2階層までをパッケージ名に反映
3. 内部パッケージは自動的に@internalスコープを付与

## 言語別の適用

各言語のイディオムに合わせた変換：

```python
# Python: アンダースコア変換
from database_postgres import Client
from internal.api_gateway import Gateway
```

```javascript
// JavaScript: そのまま使用
import { Client } from 'database-postgres'
import { Gateway } from '@internal/api-gateway'
```

```go
// Go: モジュールパスに変換
import "github.com/company/database-postgres"
import "github.com/company/internal/api-gateway"
```

## Nix Flakeでの適用

```nix
{
  # パッケージ定義
  packages = {
    database-postgres = ...;
    auth-jwt = ...;
    utils-string = ...;
  };
  
  # 内部パッケージはoverlayで提供
  overlays.default = final: prev: {
    internal = {
      api-gateway = ...;
      database-adapter = ...;
    };
  };
}
```

## 命名ガイドライン

### DO
- ✅ 機能を明確に表す名前を使用
- ✅ ハイフン（-）で単語を区切る
- ✅ 小文字のみ使用
- ✅ 文脈（context）を含める

### DON'T
- ❌ 曖昧な名前（utils、helpers、common）を単独で使用
- ❌ バージョン番号をパッケージ名に含める
- ❌ 言語固有の拡張子やサフィックス（-py、-js等）
- ❌ 3階層以上の深いネスト

## 移行戦略

1. 新規パッケージ：この規約に従って命名
2. 既存パッケージ：エイリアスを作成して段階的に移行
3. 外部依存：そのまま使用（強制しない）

## 名前の一意性保証

- 公開パッケージ：コミュニティレビューによる承認
- 内部パッケージ：スコープによる名前空間分離
- 予約語：system-、stdlib-、core- は将来の拡張用に予約

## 関連規約

- [ファイル命名規約](./file_naming.md) - ファイルレベルの命名規則