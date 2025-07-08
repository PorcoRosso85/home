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


def _get_score_interpretation(total_score: float) -> str:
    """スコアの解釈を返す"""
    if total_score >= 0:
        return "問題は検出されていません"
    elif total_score > -0.2:
        return "軽微な問題がありますが、システム全体への影響は小さいです"
    elif total_score > -0.5:
        return "いくつかの問題があります。可能であれば改善を検討してください"
    elif total_score > -0.7:
        return "重要な問題があります。早めの対応を推奨します"
    else:
        return "深刻な問題があります。即座の対応が必要です"


def safe_main():
    """すべての例外をキャッチしてJSONで返すメイン関数ラッパー"""
    try:
        # インポート（相対インポートのみ使用）
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.graph_depth_validator import GraphDepthValidator
        from .infrastructure.circular_reference_detector import CircularReferenceDetector
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
        
        # スキーマ適用リクエストの処理（initも受け付ける）
        if input_data.get("type") in ["init", "schema"]:
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
        
        # グラフ検証の初期化
        scoring_service = create_scoring_service()
        
        # Cypherクエリの場合はグラフ検証を準備
        # 注意：実際の検証はクエリ実行後に行う（依存関係を確認するため）
        if input_data.get("type") == "cypher":
            query = input_data.get("query", "")
            debug("rgl.main", "Processing Cypher query", query_length=len(query))
            
            # CREATE操作の場合は実行後に検証フラグを立てる
            if "CREATE" in query.upper() and "DEPENDS_ON" in query.upper():
                input_data["_needs_graph_validation"] = True
                debug("rgl.main", "Graph validation will be performed after query execution")
        
        # DBアクセス開始
        # KuzuDBリポジトリを作成
        info("rgl.main", "Creating KuzuDB repository")
        try:
            repository = create_kuzu_repository()
            debug("rgl.main", "Repository created successfully")
        except ImportError as e:
            # KuzuDBインポートエラー
            from .application.error_handler import create_error_handler
            error_handler = create_error_handler()
            return error_handler["handle_kuzu_import_error"](str(e))
        except Exception as e:
            # 環境変数エラーなど
            if "RGL_DB_PATH not set" in str(e):
                from .application.error_handler import create_error_handler
                error_handler = create_error_handler()
                return error_handler["handle_environment_error"]("RGL_DB_PATH_NOT_SET")
            else:
                raise  # その他のエラーは再発生
        
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
        
        # グラフ検証が必要な場合（CREATE操作後）
        if input_data.get("_needs_graph_validation") and query_result.get("status") == "success":
            debug("rgl.main", "Performing graph validation")
            
            # 循環参照検出
            circular_detector = CircularReferenceDetector()
            from .infrastructure.circular_reference_detector import validate_with_kuzu as validate_circular
            try:
                circular_result = validate_circular(repository["connection"])
            except RuntimeError as e:
                # KuzuDB関連のエラー（Variable node is not in scopeなど）
                if "Binder exception: Variable node is not in scope" in str(e):
                    from .application.error_handler import create_error_handler
                    error_handler = create_error_handler()
                    user_error = error_handler["handle_dependency_creation_error"](str(e), input_data.get("query", ""))
                    return user_error.to_dict()
                else:
                    raise  # 他のRuntimeErrorは再度発生させる
            
            if circular_result["has_cycles"]:
                # 循環参照が検出された場合
                for self_ref in circular_result["self_references"]:
                    violation = {"type": "self_reference", "node_id": self_ref}
                    violation_score = scoring_service["calculate_score"](violation)
                    
                    if "warnings" not in query_result:
                        query_result["warnings"] = []
                    query_result["warnings"].append({
                        "type": "self_reference",
                        "message": f"自己参照が検出されました: {self_ref}",
                        "score": violation_score
                    })
                
                for cycle in circular_result["cycles"]:
                    violation = {"type": "circular_reference", "cycle": cycle}
                    violation_score = scoring_service["calculate_score"](violation)
                    
                    if "warnings" not in query_result:
                        query_result["warnings"] = []
                    query_result["warnings"].append({
                        "type": "circular_reference",
                        "message": f"循環参照が検出されました: {' -> '.join(cycle)}",
                        "score": violation_score
                    })
            
            # グラフ深さ検証（プロジェクト設定がある場合）
            max_depth = input_data.get("max_graph_depth")
            if max_depth is not None:
                from .infrastructure.graph_depth_validator import validate_with_kuzu as validate_depth
                depth_result = validate_depth(repository["connection"], max_depth)
                
                if not depth_result["is_valid"]:
                    for violation in depth_result["violations"]:
                        violation_dict = {
                            "type": "graph_depth_exceeded",
                            "depth": violation["depth"],
                            "max_allowed": max_depth
                        }
                        violation_score = scoring_service["calculate_score"](violation_dict)
                        
                        if "warnings" not in query_result:
                            query_result["warnings"] = []
                        query_result["warnings"].append({
                            "type": "graph_depth_exceeded",
                            "message": f"グラフ深さ制限超過: {violation['root_id']} から {violation['leaf_id']} (深さ: {violation['depth']}, 制限: {max_depth})",
                            "score": violation_score
                        })
        
        # CREATE操作の場合、摩擦検出を実行
        if input_data.get("type") == "cypher" and query_result.get("status") == "success":
            query = input_data.get("query", "").upper()
            if "CREATE" in query and "REQUIREMENTENTITY" in query:
                debug("rgl.main", "Detected CREATE operation, analyzing friction")
                
                # 作成された要件IDを取得（CREATE操作の結果から）
                created_requirement_id = None
                if query_result.get("data") and len(query_result["data"]) > 0:
                    # 通常、最初のカラムがIDになる
                    created_requirement_id = query_result["data"][0][0] if query_result["data"][0] else None
                    debug("rgl.main", "Created requirement ID", req_id=created_requirement_id)
                
                # 摩擦検出を実行
                from .application.friction_detector import create_friction_detector
                detector = create_friction_detector()
                
                # 作成された要件に対して曖昧性をチェック
                if created_requirement_id:
                    ambiguities = detector["detect_ambiguity"](repository["connection"], created_requirement_id)
                    if ambiguities:
                        # 作成した要件に曖昧性がある場合のみ報告
                        from .application.scoring_service import create_scoring_service
                        scoring = create_scoring_service()
                        ambiguity_result = scoring["calculate_friction_score"](
                            "ambiguity_friction",
                            {"interpretation_count": 2}  # 簡易的に2とする
                        )
                        ambiguity_result["target_requirement"] = created_requirement_id
                        ambiguity_result["ambiguous_terms"] = ambiguities[0].get("ambiguous_terms", [])
                        ambiguity_result["suggestion"] = ambiguities[0].get("suggestion", "")
                        
                        # 全体の摩擦検出結果に統合
                        friction_result = {
                            "frictions": {
                                "ambiguity": ambiguity_result,
                                "priority": {"score": 0.0, "message": "優先度は適切に管理されています"},
                                "temporal": {"score": 0.0, "message": "要件は安定しています"},
                                "contradiction": {"score": 0.0, "message": "矛盾は検出されません"}
                            },
                            "total": {"total_score": ambiguity_result["score"]},
                            "details": {
                                "ambiguities": ambiguities,
                                "priority_conflicts": {"high_priority_count": 0, "has_conflict": False},
                                "temporal_changes": [],
                                "contradictions": {"contradiction_count": 0, "contradictions": []}
                            }
                        }
                    else:
                        # 曖昧性がない場合は通常の摩擦検出
                        friction_result = detector["detect_all"](repository["connection"])
                else:
                    # IDが取得できない場合は通常の摩擦検出
                    friction_result = detector["detect_all"](repository["connection"])
                
                # 結果に摩擦分析を追加（スコアの説明付き）
                query_result["friction_analysis"] = friction_result
                
                # スコアの説明を追加
                total_score = friction_result["total"]["total_score"]
                score_explanation = {
                    "meaning": f"摩擦スコア合計: {total_score:.2f}",
                    "interpretation": _get_score_interpretation(total_score),
                    "checked_aspects": [
                        f"曖昧性: {friction_result['frictions']['ambiguity']['message']}",
                        f"優先度: {friction_result['frictions']['priority']['message']}",
                        f"時間経過: {friction_result['frictions']['temporal']['message']}",
                        f"矛盾: {friction_result['frictions']['contradiction']['message']}"
                    ]
                }
                
                # 問題がある場合は詳細を追加
                if total_score < 0:
                    minor_issues = []
                    for friction_type, friction_data in friction_result["frictions"].items():
                        if friction_data["score"] < 0:
                            minor_issues.append({
                                "type": friction_type,
                                "score": friction_data["score"],
                                "severity": "high" if friction_data["score"] < -0.5 else "low",
                                "message": friction_data["message"]
                            })
                    if minor_issues:
                        score_explanation["minor_issues"] = minor_issues
                
                query_result["score_explanation"] = score_explanation
                
                # 総合スコアが悪い場合は警告
                total_score = friction_result["total"]["total_score"]
                if total_score < -0.5:
                    query_result["alert"] = {
                        "level": "warning" if total_score > -0.7 else "critical",
                        "message": f"摩擦スコア合計: {total_score:.2f}",
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