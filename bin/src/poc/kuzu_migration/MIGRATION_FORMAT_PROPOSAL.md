# マイグレーション形式の提案

## Cypherネイティブ形式を推奨する理由

### 1. **KuzuDBネイティブ**
```cypher
-- migrations/20240701_100000_add_user_email.cypher
-- Migration: Add email column to users
-- Author: dev-team
-- Date: 2024-07-01

ALTER TABLE User ADD email STRING DEFAULT '';
```

### 2. **シンプルで直接的**
- SQLライクで読みやすい
- 追加の変換層が不要
- エディタのシンタックスハイライトが効く

### 3. **EXPORT DATABASEとの整合性**
- KuzuDBが生成する`schema.cypher`と同じ形式
- 学習コスト削減
- ツールチェーンの統一

## 提案する構造

```
migrations/
├── 000_initial/
│   └── schema.cypher          # EXPORT DATABASE --schema-only の出力
├── 001_add_user_email.cypher
├── 002_add_metadata.cypher
└── 003_create_products.cypher
```

## メタデータの管理

```cypher
-- migrations/001_add_user_email.cypher
/*
 * Migration ID: 001_add_user_email
 * Description: Add email field to User table
 * Author: dev-team
 * Date: 2024-07-01
 * Rollback: ALTER TABLE User DROP email;
 */

ALTER TABLE User ADD email STRING DEFAULT '';
```

## 実装例

```python
class CypherMigration:
    def parse_migration(self, filepath: Path) -> Dict:
        with open(filepath) as f:
            content = f.read()
        
        # メタデータをコメントから抽出
        metadata = self.extract_metadata(content)
        
        # Cypher文を抽出
        statements = self.extract_statements(content)
        
        return {
            'id': filepath.stem,
            'metadata': metadata,
            'statements': statements
        }
```

## 利点まとめ

1. **ネイティブ**: KuzuDBの標準形式
2. **透明性**: 何が実行されるか明確
3. **簡潔性**: 余計な抽象化なし
4. **互換性**: 既存のCypherツールと連携可能
5. **Version Control**: diffが見やすい

JSONは構造化には優れていますが、この用途ではCypherの方が自然で実用的です。