# Priority フィールドの UINT8 リファクタリング計画

## 概要

priorityフィールドを文字列からUINT8に変更し、パフォーマンスと型安全性を向上させる。

## マッピング仕様

| 文字列値 | UINT8値 | 意味 |
|---------|---------|------|
| 'low' | 0 | 低優先度 |
| 'medium' | 1 | 中優先度（デフォルト） |
| 'high' | 2 | 高優先度 |
| 'critical' | 3 | 最重要 |

## 修正が必要なファイル一覧

### 1. スキーマ定義 (最優先)

#### `/home/nixos/bin/src/requirement/graph/ddl/schema.cypher`
```diff
- priority STRING DEFAULT 'medium',
+ priority UINT8 DEFAULT 1,
```

### 2. 摩擦検出ロジック

#### `/home/nixos/bin/src/requirement/graph/application/friction_detector.py`
```diff
# 優先度摩擦の検出
- MATCH (r:RequirementEntity {priority: 'critical'})
+ MATCH (r:RequirementEntity {priority: 3})
```

### 3. E2Eテスト

#### `/home/nixos/bin/src/requirement/graph/test_e2e_team_friction_scenarios.py`
```diff
# 複数箇所
- priority: 'high',
+ priority: 2,

- priority: 'critical',
+ priority: 3,
```

#### `/home/nixos/bin/src/requirement/graph/test_e2e_startup_cto_journey.py`
```diff
# 要件作成部分
- priority: 'high',
+ priority: 2,
```

### 4. 統合テスト

#### `/home/nixos/bin/src/requirement/graph/test_friction_detection_integration.py`
```diff
# 摩擦検出部分
- priority: 'critical'
+ priority: 3

- priority: 'high'  
+ priority: 2

- priority: 'medium'
+ priority: 1
```

### 5. 新規作成が必要なファイル

#### `/home/nixos/bin/src/requirement/graph/application/priority_mapper.py`
```python
"""
Priority の文字列とUINT8の相互変換
"""
from typing import Union


class PriorityMapper:
    """優先度の文字列とUINT8値のマッピング"""
    
    STRING_TO_UINT8 = {
        'low': 0,
        'medium': 1,
        'high': 2,
        'critical': 3
    }
    
    UINT8_TO_STRING = {
        0: 'low',
        1: 'medium',
        2: 'high',
        3: 'critical'
    }
    
    @classmethod
    def to_uint8(cls, value: Union[str, int]) -> int:
        """文字列またはintをUINT8に変換"""
        if isinstance(value, int):
            if 0 <= value <= 3:
                return value
            raise ValueError(f"Invalid priority value: {value}")
        
        if value not in cls.STRING_TO_UINT8:
            raise ValueError(f"Unknown priority string: {value}")
        return cls.STRING_TO_UINT8[value]
    
    @classmethod
    def to_string(cls, value: int) -> str:
        """UINT8を文字列に変換"""
        if value not in cls.UINT8_TO_STRING:
            raise ValueError(f"Invalid priority value: {value}")
        return cls.UINT8_TO_STRING[value]
    
    @classmethod
    def is_critical(cls, value: Union[str, int]) -> bool:
        """critical（最重要）かどうかを判定"""
        if isinstance(value, str):
            return value == 'critical'
        return value == 3
```

#### `/home/nixos/bin/src/requirement/graph/migrations/priority_string_to_uint8.py`
```python
"""
既存の文字列priorityをUINT8に移行するスクリプト
"""
import kuzu


def migrate_priority_data(connection: kuzu.Connection) -> bool:
    """既存データの priority を文字列から UINT8 に変換"""
    try:
        # 一時テーブルを作成
        connection.execute("""
            CREATE NODE TABLE RequirementEntity_new (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                priority UINT8 DEFAULT 1,
                requirement_type STRING DEFAULT 'functional',
                status STRING DEFAULT 'proposed',
                verification_required BOOLEAN DEFAULT true,
                implementation_details STRING,
                acceptance_criteria STRING,
                technical_specifications STRING
            )
        """)
        
        # データをコピー（priorityを変換）
        connection.execute("""
            INSERT INTO RequirementEntity_new
            SELECT 
                id, title, description,
                CASE priority
                    WHEN 'low' THEN 0
                    WHEN 'medium' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'critical' THEN 3
                    ELSE 1  -- デフォルト: medium
                END as priority,
                requirement_type, status, verification_required,
                implementation_details, acceptance_criteria, technical_specifications
            FROM RequirementEntity
        """)
        
        # テーブルを入れ替え
        connection.execute("DROP TABLE RequirementEntity")
        connection.execute("ALTER TABLE RequirementEntity_new RENAME TO RequirementEntity")
        
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
```

## 移行手順

1. **TDDテストの実行（Red）**
   ```bash
   ./test.sh test_priority_refactoring.py
   ```

2. **スキーマ変更**
   - `schema.cypher` を修正
   - または `schema_uint8.cypher` を新規作成

3. **コア機能の修正**
   - `priority_mapper.py` を作成
   - `friction_detector.py` を修正

4. **テストの修正**
   - 各テストファイルのpriority値を更新

5. **移行スクリプトの作成と実行**
   - `priority_string_to_uint8.py` を作成
   - 既存データを移行

6. **後方互換性の確保（オプション）**
   - API層で文字列入力を受け付けて内部で変換

## 影響範囲

### 高影響
- DDLスキーマ
- 摩擦検出ロジック（critical count）
- 比較クエリ（>= など）

### 中影響
- E2Eテスト
- 統合テスト
- サンプルデータ

### 低影響
- ドキュメント
- コメント内の例

## 性能向上の期待値

- **クエリ性能**: 文字列比較からINT比較になり高速化
- **ストレージ**: 文字列からUINT8で容量削減
- **型安全性**: 不正な値の混入を防止

## ロールバック計画

万が一問題が発生した場合：
1. スキーマを元に戻す
2. 逆移行スクリプトで UINT8 → 文字列に変換
3. コードを元のバージョンに戻す