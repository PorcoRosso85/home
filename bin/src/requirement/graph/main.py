"""
Requirement Graph - Cypherクエリエントリーポイント

使い方:
    echo '{"type": "cypher", "query": "CREATE ..."}' | python -m requirement.graph.main
    echo '{"type": "schema", "action": "apply"}' | python -m requirement.graph.main
    
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
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.hierarchy_validator import HierarchyValidator
        from .infrastructure.variables import get_db_path
        from .infrastructure.logger import debug, info, warn, error, result, score
        from .infrastructure.query_validator import QueryValidator
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        from .application.scoring_service import create_scoring_service
        
        info("rgl.main", "Starting main function")
        
        # 標準入力からJSONを読む
        stdin_data = sys.stdin.read()
        debug("rgl.main", f"Received input", length=len(stdin_data))
        input_data = json.loads(stdin_data)
        debug("rgl.main", f"Parsed JSON", type=input_data.get("type"))
        
        # スキーマ適用リクエストの処理
        if input_data.get("type") == "schema":
            debug("rgl.main", "Processing schema request")
            from .infrastructure.apply_ddl_schema import apply_ddl_schema
            
            action = input_data.get("action", "apply")
            if action == "apply":
                db_path = input_data.get("db_path")
                create_test_data = input_data.get("create_test_data", False)
                
                success = apply_ddl_schema(db_path=db_path, create_test_data=create_test_data)
                
                if success:
                    result({"message": "Schema applied successfully"}, metadata={"status": "success"})
                else:
                    error("Failed to apply schema", score=-1.0)
                return
            else:
                error(f"Unknown schema action: {action}", score=-1.0)
                return
        
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
                error(
                    hierarchy_result["error"],
                    details=hierarchy_result["details"],
                    score=score
                )
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
        
        # バージョニングとクエリバリデーション
        enable_versioning = input_data.get("enable_versioning", True)
        validator = QueryValidator()
        
        # クエリタイプのチェック（現在はcypherのみサポート）
        query_type = input_data.get("type", "cypher")
        if query_type != "cypher":
            query_result = {
                "status": "error",
                "error": f"Unsupported query type: {query_type}",
                "supported_types": ["cypher"]
            }
        else:
            # Cypherクエリの処理
            query_str = input_data.get("query", "")
            params = input_data.get("parameters", {})
            
            # クエリ検証
            is_valid, validation_error = validator.validate(query_str)
            if not is_valid:
                query_result = {
                    "status": "error",
                    "error": "Query validation failed",
                    "details": validation_error
                }
            else:
                # バージョニングの有無で実行を切り替え
                if enable_versioning:
                    versioned_executor = create_versioned_cypher_executor(repository)
                    query_result = versioned_executor["execute"](input_data)
                else:
                    # 通常のクエリ実行
                    query_result = repository["execute"](query_str, params)
        
        info("rgl.main", "Query completed", status=query_result.get("status"))
        debug("rgl.main", "Query completed", status=query_result.get("status"))
        
        # 階層警告を結果に含める
        if "_hierarchy_warning" in input_data:
            query_result["warning"] = input_data["_hierarchy_warning"]
            query_result["score"] = max(query_result.get("score", 0.0), input_data["_hierarchy_score"])
        
        # CREATE操作の場合、摩擦検出を実行
        if input_data.get("type") == "cypher" and query_result.get("status") == "success":
            query = input_data.get("query", "").upper()
            if "CREATE" in query and "REQUIREMENTENTITY" in query:
                debug("rgl.main", "Detected CREATE operation, analyzing friction")
                
                # 摩擦検出を実行
                from .application.friction_detector import create_friction_detector
                detector = create_friction_detector()
                friction_result = detector["detect_all"](repository["connection"])
                
                # 結果に摩擦分析を追加
                query_result["friction_analysis"] = friction_result
                
                # 総合スコアが悪い場合は警告
                total_score = friction_result["total"]["total_score"]
                if total_score < -0.5:
                    query_result["alert"] = {
                        "level": "warning" if total_score > -0.7 else "critical",
                        "message": f"プロジェクトの健全性: {friction_result['total']['health']}",
                        "score": total_score
                    }
                    
                # 個別の摩擦で深刻なものがあれば詳細を提供
                for friction_type, friction_data in friction_result["frictions"].items():
                    if friction_data["score"] < -0.5:
                        if "friction_details" not in query_result:
                            query_result["friction_details"] = []
                        query_result["friction_details"].append({
                            "type": friction_type,
                            "score": friction_data["score"],
                            "message": friction_data["message"]
                        })
        
        # 結果の出力
        if query_result.get("status") == "success":
            # 成功時の出力
            result_data = query_result.get("data", [])
            metadata = query_result.get("metadata", {})
            
            # 結果を出力
            result(result_data, metadata=metadata)
            
            # 摩擦分析がある場合はスコアとして出力
            if "friction_analysis" in query_result:
                score(query_result["friction_analysis"])
            
            # アラートがある場合
            if "alert" in query_result:
                warn("rgl.main", query_result["alert"]["message"], 
                     level=query_result["alert"]["level"],
                     score=query_result["alert"]["score"])
        else:
            # エラー時の出力
            error(
                query_result.get("message", "Unknown error"),
                details=query_result.get("details"),
                score=query_result.get("score", -1.0)
            )
        
    except json.JSONDecodeError as e:
        # JSONパースエラー
        error("Invalid JSON input", details={"error": str(e)})
    except ImportError as e:
        # インポートエラー
        error("Module import failed", details={"error": str(e)})
    except Exception as e:
        # その他のエラー
        import traceback
        error(str(e), details={"error_type": type(e).__name__, "traceback": traceback.format_exc()})


def main():
    """エントリーポイント - すべての例外を確実にキャッチ"""
    try:
        safe_main()
    except BaseException as e:
        # 最終的なセーフティネット（KeyboardInterruptなども含む）
        error(
            "Critical error occurred",
            details={"error_type": type(e).__name__, "error": str(e)},
            score=-1.0
        )
        # BaseExceptionはsys.exitなども含むため、再raiseはしない


if __name__ == "__main__":
    main()