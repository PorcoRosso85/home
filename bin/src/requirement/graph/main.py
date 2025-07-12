"""
Requirement Graph - Cypherクエリエントリーポイント

使い方:
    echo '{"type": "cypher", "query": "CREATE ..."}' | python -m requirement.graph.main
    echo '{"type": "schema", "action": "apply"}' | python -m requirement.graph.main

戻り値:
    {"status": "success|error", "message": "..."}
"""
import sys
import json


def safe_main():
    """すべての例外をキャッチしてJSONで返すメイン関数ラッパー"""
    # エラー関数を先に定義（import失敗時にも使用するため）
    def emergency_error(message: str, **kwargs):
        import json
        output = {"type": "error", "level": "error", "message": message}
        output.update(kwargs)
        print(json.dumps(output, ensure_ascii=False), flush=True)

    error = emergency_error  # デフォルトでemergency_errorを使用

    try:
        # インポート（相対インポートのみ使用）
        from .infrastructure.kuzu_repository import create_kuzu_repository
        from .infrastructure.graph_depth_validator import GraphDepthValidator
        from .infrastructure.circular_reference_detector import CircularReferenceDetector
        from .infrastructure.variables import get_db_path
        from .infrastructure.logger import debug, info, warn, error, result
        # Removed imports for deleted modules (query_validator, versioned_cypher_executor)

        info("rgl.main", "Starting main function")

        db_path = get_db_path()
        repository = create_kuzu_repository(db_path)

        # 入力データの読み込み
        input_data = json.load(sys.stdin)
        input_type = input_data.get("type", "cypher")

        if input_type == "schema":
            # スキーマ管理
            action = input_data.get("action", "apply")
            if action == "apply":
                from .infrastructure.apply_ddl_schema import apply_ddl_schema
                info("rgl.main", "Applying DDL schema", action=action)
                apply_ddl_schema(db_path, input_data.get("create_test_data", False))
                result({"status": "success", "message": "Schema applied"})
            else:
                error("Unknown schema action", details={"action": action})

        elif input_type == "template":
            # テンプレート処理
            from .application.template_processor import process_template
            
            info("rgl.main", "Processing template", template=input_data.get("template"))
            query_result = process_template(input_data, repository)
            
            # エラーチェック
            if "error" in query_result:
                query_result["status"] = "error"
            else:
                query_result["status"] = "success"
                
            info("rgl.main", "Template completed", status=query_result.get("status"))
            
            # 結果を出力
            result(query_result)
            
        elif input_type == "cypher":
            # Cypherクエリ実行
            query_str = input_data.get("query", "")
            params = input_data.get("parameters", {})

            # 直接クエリを実行（検証とバージョニングは削除）
            query_result = repository["execute"](query_str, params)

            # エラーチェック
            if "error" in query_result:
                query_result["status"] = "error"
            else:
                query_result["status"] = "success"

            info("rgl.main", "Query completed", status=query_result.get("status"))

            # リスク評価（スコアは出力しない）
            # TODO: GraphDepthValidator と CircularReferenceDetector の実装を修正する必要がある
            # if query_result.get("status") == "success":
            #     # グラフ深さチェック
            #     depth_validator = GraphDepthValidator(repository["connection"])
            #     depth_issues = depth_validator.validate()
            #
            #     # 循環参照チェック
            #     circular_detector = CircularReferenceDetector(repository["connection"])
            #     circular_issues = circular_detector.detect()
            #
            #     # 問題がある場合は issues として追加
            #     all_issues = depth_issues + circular_issues
            #     if all_issues:
            #         query_result["issues"] = all_issues
            #
            #     debug("rgl.main", "Risk assessment completed",
            #           issue_count=len(all_issues))

            # 結果を出力
            result(query_result)


        elif input_type == "semantic_search":
            # 意味的検索機能
            from ..domain.embedder import Embedder

            query_text = input_data.get("query", "")
            threshold = input_data.get("threshold", 0.5)
            limit = input_data.get("limit", 10)

            if not query_text:
                error("query is required for semantic search")
            else:
                info("rgl.main", "Starting semantic search",
                     query=query_text[:50], threshold=threshold)

                embedder = Embedder()

                # クエリテキストのベクトル化
                query_vector = embedder.encode(query_text)

                # ベクトル検索実行
                search_result = repository["semantic_search"](
                    query_vector, threshold, limit
                )

                if search_result["status"] == "success":
                    # 結果を出力
                    result({
                        "status": "success",
                        "data": search_result["data"],
                        "count": len(search_result["data"])
                    })
                else:
                    error("Semantic search failed", details=search_result)


        elif input_type == "version":
            # Version service removed (use Git for versioning)
            error("Version service has been removed. Please use Git for version control.")
            
        else:
            error("Unknown input type", details={"type": input_type})

        # クローズ処理は不要（KuzuDBは自動的にクローズされる）

    except json.JSONDecodeError as e:
        # JSONパースエラー
        error("Invalid JSON input", details={"error": str(e)})
    except ImportError as e:
        # インポートエラー
        emergency_error("Module import failed", details={"error": str(e)})
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
        import json
        print(json.dumps({
            "type": "error",
            "level": "error",
            "message": "Unexpected error in main()",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
