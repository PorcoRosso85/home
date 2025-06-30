"""
Requirement Graph - LLM専用エントリーポイント

使い方:
    echo '{"type": "cypher", "query": "CREATE ..."}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ python -m requirement.graph.main
    
戻り値:
    {"status": "success|error", "score": -1.0~1.0, "message": "..."}
"""
import sys
import json
import os


def safe_main():
    """すべての例外をキャッチしてJSONで返すメイン関数ラッパー"""
    try:
        # インポート（相対インポートのみ使用）
        from .infrastructure.llm_hooks_api import create_llm_hooks_api
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.hierarchy_validator import HierarchyValidator
        from .infrastructure.variables import get_db_path
        from .infrastructure.logger import debug, info, warn, error
        from .application.scoring_service import create_scoring_service
        
        info("rgl.main", "Starting main function")
        
        # 標準入力からJSONを読む
        stdin_data = sys.stdin.read()
        debug("rgl.main", f"Received input", length=len(stdin_data))
        input_data = json.loads(stdin_data)
        debug("rgl.main", f"Parsed JSON", type=input_data.get("type"))
        
        # 階層検証は最初に実行（DBアクセス前）
        hierarchy_validator = HierarchyValidator()
        scoring_service = create_scoring_service()
        
        # Cypherクエリの場合は階層検証を実行
        if input_data.get("type") == "cypher":
            query = input_data.get("query", "")
            debug("rgl.main", "Processing Cypher query", query_length=len(query))
            
            # 階層検証
            hierarchy_result = hierarchy_validator.validate_hierarchy_constraints(query)
            debug("rgl.main", "Hierarchy validation result", is_valid=hierarchy_result["is_valid"], violation_type=hierarchy_result["violation_type"])
            
            if not hierarchy_result["is_valid"]:
                # 違反情報をスコアリングサービスに渡してスコアを計算
                violation = {
                    "type": hierarchy_result["violation_type"],
                    **hierarchy_result.get("violation_info", {})
                }
                score = scoring_service["calculate_score"](violation)
                
                # 階層違反 - 負のフィードバック
                response = {
                    "status": "error",
                    "score": score,
                    "message": hierarchy_result["error"],
                    "details": hierarchy_result["details"],
                    "suggestion": "階層ルールに従ってください。親は子より上位の階層である必要があります。"
                }
                print(json.dumps(response, ensure_ascii=False))
                return
            
            # 警告がある場合
            if hierarchy_result["warning"]:
                # 違反情報をスコアリングサービスに渡してスコアを計算
                violation = {
                    "type": hierarchy_result["violation_type"],
                    **hierarchy_result.get("violation_info", {})
                }
                score = scoring_service["calculate_score"](violation)
                
                # クエリは実行するが、警告を含める
                input_data["_hierarchy_warning"] = hierarchy_result["warning"]
                input_data["_hierarchy_score"] = score
        
        # 階層検証を通過した場合のみDBアクセス
        # KuzuDBリポジトリを作成
        info("rgl.main", "Creating KuzuDB repository")
        repository = create_kuzu_repository()
        debug("rgl.main", "Repository created successfully")
        
        # 階層検証機能を統合したAPIを作成
        api = create_llm_hooks_api(repository)
        debug("rgl.main", "API created successfully")
        
        # APIを実行
        info("rgl.main", "Executing API query")
        result = api["query"](input_data)
        debug("rgl.main", "API query completed", status=result.get("status"))
        
        # 階層警告を結果に含める
        if "_hierarchy_warning" in input_data:
            result["warning"] = input_data["_hierarchy_warning"]
            result["score"] = max(result.get("score", 0.0), input_data["_hierarchy_score"])
        
        # CREATE操作の場合、摩擦検出を実行
        if input_data.get("type") == "cypher" and result.get("status") == "success":
            query = input_data.get("query", "").upper()
            if "CREATE" in query and "REQUIREMENTENTITY" in query:
                debug("rgl.main", "Detected CREATE operation, analyzing friction")
                
                # 摩擦検出を実行
                from .application.friction_detector import create_friction_detector
                detector = create_friction_detector()
                friction_result = detector["detect_all"](repository["connection"])
                
                # 結果に摩擦分析を追加
                result["friction_analysis"] = friction_result
                
                # 総合スコアが悪い場合は警告
                total_score = friction_result["total"]["total_score"]
                if total_score < -0.5:
                    result["alert"] = {
                        "level": "warning" if total_score > -0.7 else "critical",
                        "message": f"プロジェクトの健全性: {friction_result['total']['health']}",
                        "recommendation": friction_result["total"]["recommendation"],
                        "score": total_score
                    }
                    
                # 個別の摩擦で深刻なものがあれば詳細を提供
                for friction_type, friction_data in friction_result["frictions"].items():
                    if friction_data["score"] < -0.5:
                        if "friction_details" not in result:
                            result["friction_details"] = []
                        result["friction_details"].append({
                            "type": friction_type,
                            "score": friction_data["score"],
                            "message": friction_data["message"]
                        })
        
        output = json.dumps(result, ensure_ascii=False)
        debug("rgl.main", "Sending response", response_length=len(output))
        print(output)
        
    except json.JSONDecodeError as e:
        # JSONパースエラー
        error_response = {
            "status": "error",
            "message": "Invalid JSON input",
            "details": str(e),
            "suggestion": "正しいJSON形式で入力してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))
    except ImportError as e:
        # インポートエラー
        error_response = {
            "status": "error",
            "message": "Module import failed",
            "details": str(e),
            "suggestion": "実行環境を確認してください。python -m requirement.graph.main として実行してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))
    except Exception as e:
        # その他のエラー
        error_response = {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "suggestion": "エラーが発生しました。クエリを確認してください"
        }
        print(json.dumps(error_response, ensure_ascii=False))


def main():
    """エントリーポイント - すべての例外を確実にキャッチ"""
    try:
        safe_main()
    except BaseException as e:
        # 最終的なセーフティネット（KeyboardInterruptなども含む）
        error_response = {
            "status": "error",
            "score": -1.0,
            "message": "Critical error occurred",
            "error_type": type(e).__name__,
            "details": str(e)
        }
        print(json.dumps(error_response, ensure_ascii=False))
        # BaseExceptionはsys.exitなども含むため、再raiseはしない


if __name__ == "__main__":
    main()