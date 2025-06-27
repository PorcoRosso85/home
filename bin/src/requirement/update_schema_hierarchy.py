#!/usr/bin/env python3
"""
スキーマ更新スクリプト
RequirementEntityにhierarchy_levelとhierarchy_nameプロパティを追加
"""
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# 環境変数設定
os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"

from graph.infrastructure.cypher_executor import CypherExecutor


def update_schema():
    """スキーマを更新してhierarchy関連プロパティを追加"""
    # KuzuDB接続
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kuzu", 
        "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
    )
    kuzu = importlib.util.module_from_spec(spec)
    sys.modules['kuzu'] = kuzu
    spec.loader.exec_module(kuzu)
    
    db = kuzu.Database("/home/nixos/bin/src/kuzu/kuzu_db")
    conn = kuzu.Connection(db)
    executor = CypherExecutor(conn)
    
    print("=== スキーマ更新開始 ===\n")
    
    # 1. 既存のRequirementEntityの構造を確認
    print("1. 既存のテーブル構造を確認:")
    try:
        # KuzuDBではALTER TABLEがサポートされていない可能性があるため、
        # 既存データに新しいプロパティを追加する別の方法を使用
        
        # まず、既存の要件数を確認
        count_result = executor.execute("""
            MATCH (r:RequirementEntity)
            RETURN count(r) as count
        """)
        
        req_count = count_result["data"][0][0] if count_result.get("data") else 0
        print(f"  既存の要件数: {req_count}件")
        
        # 2. 新しいプロパティを既存のノードに追加
        print("\n2. hierarchy_levelとhierarchy_nameプロパティを追加:")
        
        # 全ての要件ノードに新しいプロパティを追加（初期値はNULL）
        update_result = executor.execute("""
            MATCH (r:RequirementEntity)
            SET r.hierarchy_level = NULL,
                r.hierarchy_name = NULL,
                r.estimated_hierarchy_type = NULL
            RETURN count(r) as updated_count
        """)
        
        if update_result.get("data"):
            updated = update_result["data"][0][0]
            print(f"  ✓ {updated}件の要件にプロパティを追加しました")
        
        # 3. プロパティが正しく追加されたか確認
        print("\n3. プロパティ追加の確認:")
        verify_result = executor.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.title, r.hierarchy_level, r.hierarchy_name
            LIMIT 3
        """)
        
        if verify_result.get("data"):
            print("  サンプル要件:")
            for row in verify_result["data"]:
                print(f"    - {row[1]}: hierarchy_level={row[2]}, hierarchy_name={row[3]}")
        
        print("\n✓ スキーマ更新が完了しました")
        print("  新しいプロパティ:")
        print("  - hierarchy_level: INTEGER (階層レベル 0-4)")
        print("  - hierarchy_name: STRING (vision/architecture/module/component/task)")
        print("  - estimated_hierarchy_type: STRING (推定された階層タイプ)")
        
        return True
        
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        return False


def create_updated_schema_file():
    """更新されたスキーマファイルを生成"""
    updated_schema = """// 更新されたスキーマ定義 (v2.1) - 階層情報を追加
// RequirementEntityにhierarchy関連プロパティを追加

// ノードテーブル（エンティティ）
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING NOT NULL,
    description STRING,
    priority STRING DEFAULT 'medium',
    requirement_type STRING DEFAULT 'functional',
    verification_required BOOLEAN DEFAULT true,
    status STRING DEFAULT 'draft',
    embedding DOUBLE[50],
    created_at STRING,
    // 新規追加：階層関連プロパティ
    hierarchy_level INT32,
    hierarchy_name STRING,
    estimated_hierarchy_type STRING
);

CREATE NODE TABLE CodeEntity (
    persistent_id STRING PRIMARY KEY,
    name STRING NOT NULL,
    type STRING NOT NULL,
    signature STRING,
    complexity INT32 DEFAULT 0,
    start_position INT32,
    end_position INT32
);

CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING NOT NULL,
    description STRING,
    change_reason STRING,
    progress_percentage DOUBLE DEFAULT 0.0
);

CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,
    description STRING,
    type STRING NOT NULL,
    source_type STRING DEFAULT 'documentation'
);

// エッジテーブル（関係）
CREATE REL TABLE LOCATES_LocationURI_RequirementEntity (
    FROM LocationURI TO RequirementEntity
);

CREATE REL TABLE LOCATES_LocationURI_CodeEntity (
    FROM LocationURI TO CodeEntity
);

CREATE REL TABLE IS_IMPLEMENTED_BY (
    FROM RequirementEntity TO CodeEntity,
    confidence_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE IS_VERIFIED_BY (
    FROM RequirementEntity TO CodeEntity,
    test_coverage DOUBLE DEFAULT 0.0
);

CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity,
    dependency_type STRING DEFAULT 'requires',
    reason STRING
);

CREATE REL TABLE HAS_VERSION (
    FROM RequirementEntity TO VersionState
);

CREATE REL TABLE HAS_VERSION_CodeEntity (
    FROM CodeEntity TO VersionState
);

CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);

CREATE REL TABLE REFERENCES (
    FROM RequirementEntity TO ReferenceEntity,
    relevance_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE CONFLICTS_WITH (
    FROM RequirementEntity TO RequirementEntity,
    conflict_reason STRING
);

CREATE REL TABLE SIMILAR_TO (
    FROM RequirementEntity TO RequirementEntity,
    similarity_score DOUBLE
);

CREATE REL TABLE EXTRACTED_FROM (
    FROM RequirementEntity TO ReferenceEntity,
    extraction_confidence DOUBLE DEFAULT 1.0
);

// インデックス（オプション - KuzuDBが自動的に主キーにインデックスを作成）
// CREATE INDEX req_title_idx ON RequirementEntity(title);
// CREATE INDEX req_priority_idx ON RequirementEntity(priority);
// CREATE INDEX req_type_idx ON RequirementEntity(requirement_type);
// CREATE INDEX req_hierarchy_idx ON RequirementEntity(hierarchy_level);
// CREATE INDEX code_name_idx ON CodeEntity(name);
// CREATE INDEX code_type_idx ON CodeEntity(type);
"""
    
    with open("/home/nixos/bin/src/requirement/graph/ddl/schema_v2.1.cypher", "w") as f:
        f.write(updated_schema)
    
    print("\n更新されたスキーマファイルを作成しました:")
    print("  graph/ddl/schema_v2.1.cypher")


if __name__ == "__main__":
    # スキーマを更新
    if update_schema():
        # 更新されたスキーマファイルも作成
        create_updated_schema_file()
        
        print("\n次のステップ:")
        print("1. python dynamic_hierarchy_system.py を実行して階層レベルを自動計算")
        print("2. 階層情報がデータベースに保存されることを確認")