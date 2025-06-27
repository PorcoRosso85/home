"""
Requirement Graph - LLM専用エントリーポイント

使い方:
    echo '{"type": "cypher", "query": "CREATE ..."}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ python -m requirement.graph.main
    
戻り値:
    {"status": "success|error", "score": -1.0~1.0, "message": "..."}
"""
import sys
import json
from infrastructure.llm_hooks_api import create_llm_hooks_api
from infrastructure.kuzu_repository import create_kuzu_repository
from infrastructure.hierarchy_validator import HierarchyValidator

def main():
    """LLMからのCypherクエリを受け取り、検証・実行・フィードバックを返す"""
    try:
        # 標準入力からJSONを読む
        input_data = json.loads(sys.stdin.read())
        
        # 階層検証は最初に実行（DBアクセス前）
        hierarchy_validator = HierarchyValidator()
        
        # Cypherクエリの場合は階層検証を実行
        if input_data.get("type") == "cypher":
            query = input_data.get("query", "")
            
            # 階層検証
            hierarchy_result = hierarchy_validator.validate_hierarchy_constraints(query)
            
            if not hierarchy_result["is_valid"]:
                # 階層違反 - 負のフィードバック
                response = {
                    "status": "error",
                    "score": hierarchy_result["score"],
                    "message": hierarchy_result["error"],
                    "details": hierarchy_result["details"],
                    "suggestion": "階層ルールに従ってください。親は子より上位の階層である必要があります。"
                }
                print(json.dumps(response, ensure_ascii=False))
                return
            
            # 警告がある場合
            if hierarchy_result["warning"]:
                # クエリは実行するが、警告を含める
                input_data["_hierarchy_warning"] = hierarchy_result["warning"]
                input_data["_hierarchy_score"] = hierarchy_result["score"]
        
        # 階層検証を通過した場合のみDBアクセス
        # KuzuDBリポジトリを作成
        repository = create_kuzu_repository("./kuzu_db")
        
        # 階層検証機能を統合したAPIを作成
        api = create_llm_hooks_api(repository)
        
        # APIを実行
        result = api["query"](input_data)
        
        # 階層警告を結果に含める
        if "_hierarchy_warning" in input_data:
            result["warning"] = input_data["_hierarchy_warning"]
            result["score"] = max(result.get("score", 0.0), input_data["_hierarchy_score"])
        
        print(json.dumps(result, ensure_ascii=False))
        
    except json.JSONDecodeError:
        error_response = {
            "status": "error",
            "score": -0.5,
            "message": "Invalid JSON input",
            "suggestion": "正しいJSON形式で入力してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))
    except Exception as e:
        error_response = {
            "status": "error",
            "score": -0.5,
            "message": str(e),
            "suggestion": "エラーが発生しました。クエリを確認してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))

if __name__ == "__main__":
    main()