"""
RGLシステムのテスト実行（新規DB使用）
"""
import sys
import json
import os

# Pythonパスを設定
sys.path.insert(0, '/home/nixos/bin/src')

os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

# 新規DBを使用するように変更
from infrastructure.llm_hooks_api import create_llm_hooks_api
from infrastructure.kuzu_repository import create_kuzu_repository  
from infrastructure.hierarchy_validator import HierarchyValidator
from infrastructure.apply_ddl_schema import apply_ddl_schema

def run_command(command):
    """コマンドを実行して結果を返す"""
    try:
        # 階層検証
        hierarchy_validator = HierarchyValidator()
        
        if command.get("type") == "cypher":
            query = command.get("query", "")
            hierarchy_result = hierarchy_validator.validate_hierarchy_constraints(query)
            
            if not hierarchy_result["is_valid"]:
                return {
                    "status": "error",
                    "score": hierarchy_result["score"],
                    "message": hierarchy_result["error"],
                    "details": hierarchy_result["details"]
                }
        
        # DBアクセス
        repository = create_kuzu_repository("./test_rgl_db")
        api = create_llm_hooks_api(repository)
        result = api["query"](command)
        
        if hierarchy_result.get("warning"):
            result["warning"] = hierarchy_result["warning"]
            
        return result
        
    except Exception as e:
        return {"status": "error", "score": -0.5, "message": str(e)}

# スキーマ初期化
print("=== スキーマ初期化 ===")
apply_result = apply_ddl_schema("./test_rgl_db")
print(f"スキーマ初期化: {'成功' if apply_result else '失敗'}")
print()

# DML: 要件追加
print("=== DML: RGLシステムの要件追加 ===")

# Level 0: ビジョン
vision_cmd = {
    "type": "cypher",
    "query": """
    CREATE (vision:RequirementEntity {
        id: 'rgl_vision',
        title: 'RGL System Vision',
        description: 'LLM専用の要件管理システム',
        hierarchy_level: 0,
        status: 'approved',
        created_at: datetime(),
        embedding: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    })
    """
}

result = run_command(vision_cmd)
print(f"Level 0 ビジョン作成: {result}")
print()

# Level 1: アーキテクチャ
arch_cmd = {
    "type": "cypher",
    "query": """
    MATCH (vision:RequirementEntity {id: 'rgl_vision'})
    CREATE (arch:RequirementEntity {
        id: 'rgl_arch_3layer',
        title: '3層アーキテクチャ',
        description: 'Domain/Application/Infrastructure層による責務分離',
        hierarchy_level: 1,
        status: 'approved',
        created_at: datetime(),
        embedding: [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1,
                   0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1,
                   0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1,
                   0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1,
                   0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1]
    })
    CREATE (vision)-[:PARENT_OF]->(arch)
    """
}

result = run_command(arch_cmd)
print(f"Level 1 アーキテクチャ作成: {result}")
print()

# 階層違反テスト
print("=== 階層違反テスト ===")
violation_cmd = {
    "type": "cypher",
    "query": """
    CREATE (task:RequirementEntity {id: 'bad_task', hierarchy_level: 4})
    CREATE (vision:RequirementEntity {id: 'bad_vision', hierarchy_level: 0})
    CREATE (task)-[:PARENT_OF]->(vision)
    """
}

result = run_command(violation_cmd)
print(f"階層違反結果: {result}")
print()

# DQL: 要件読み出し
print("=== DQL: 要件の読み出し ===")

# 全要件一覧
list_cmd = {
    "type": "cypher",
    "query": """
    MATCH (r:RequirementEntity)
    RETURN r.hierarchy_level as level, r.id as id, r.title as title
    ORDER BY r.hierarchy_level
    """
}

result = run_command(list_cmd)
print(f"全要件一覧: {result}")
print()

# 階層構造
hierarchy_cmd = {
    "type": "cypher",
    "query": """
    MATCH (parent:RequirementEntity)-[:PARENT_OF]->(child:RequirementEntity)
    RETURN parent.title as parent, child.title as child
    """
}

result = run_command(hierarchy_cmd)
print(f"階層構造: {result}")