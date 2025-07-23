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
        # Removed imports for deleted validation modules
        from .infrastructure.variables import get_db_path
        from .infrastructure.logger import debug, info, warn, error, result
        # Removed imports for deleted modules (query_validator, versioned_cypher_executor)

        info("rgl.main", "Starting main function")

        db_path = get_db_path()
        if isinstance(db_path, dict) and db_path.get("type") == "EnvironmentConfigError":
            error("rgl.main", f"Environment configuration error: {db_path['message']}")
            sys.exit(1)

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
            from .application.search_adapter import SearchAdapter

            # リポジトリを作成
            repository = create_kuzu_repository(db_path)

            # Searchアダプターは遅延初期化のため、ファクトリー関数を渡す
            def create_search_service():
                """Search serviceを必要時にのみ作成"""
                try:
                    repo_connection = repository.get("connection")
                    search_service = SearchAdapter(db_path, repository_connection=repo_connection)
                    info("rgl.main", "Search adapter initialized with shared connection",
                         is_available=search_service.is_available)
                    return search_service
                except Exception as e:
                    warn("rgl.main", f"Search service initialization failed: {e}")
                    return None

            template_name = input_data.get("template")
            info("rgl.main", "Processing template", template=template_name)
            
            # 依存関係管理系のテンプレートではsearch serviceは不要
            if template_name in ["add_dependency", "find_dependencies", "remove_dependency"]:
                query_result = process_template(input_data, repository, None)
            else:
                query_result = process_template(input_data, repository, create_search_service)

            # エラーチェック
            if "error" in query_result:
                query_result["status"] = "error"
            else:
                query_result["status"] = "success"

            info("rgl.main", "Template completed", status=query_result.get("status"))

            # 結果を出力
            result(query_result)

        elif input_type == "cypher":
            # Cypher直接実行は廃止（セキュリティリスク）
            error("Cypher direct execution has been removed. Please use template input instead.")


        elif input_type == "semantic_search":
            # 意味的検索機能はsearch serviceに統合
            error("Semantic search has been integrated into search service. Use template input with duplicate check.")


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
