"""
Requirement Graph - 要件管理システム

使い方:
    echo '{"type": "schema", "action": "apply"}' | python -m requirement.graph.main
    echo '{"type": "template", "template": "create_requirement", "parameters": {...}}' | python -m requirement.graph.main

戻り値:
    {"status": "success|error", "message": "..."}
"""
import sys
import json


def _check_db_initialized(db_path: str) -> bool:
    """Check if the database is initialized"""
    import os
    from pathlib import Path
    
    if db_path == ":memory:":
        return False  # In-memory DB is never "initialized" - we always need to create schema
    
    # Check if the database file exists
    db_file_path = Path(db_path)
    if db_file_path.is_dir():
        db_file_path = db_file_path / "db.kuzu"
    
    return db_file_path.exists()


def safe_main():
    """すべての例外をキャッチしてJSONで返すメイン関数ラッパー"""
    # エラー関数を先に定義（import失敗時にも使用するため）
    def emergency_error(message: str, **kwargs):
        import json
        output = {"type": "error", "level": "error", "message": message}
        output.update(kwargs)
        # loggerが利用できない場合のため、構造化されたJSONをそのまま出力
        import sys
        sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    error = emergency_error  # デフォルトでemergency_errorを使用

    try:
        # インポート（絶対インポートに変更）
        from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
        # Removed imports for deleted validation modules
        from requirement.graph.infrastructure.variables import get_db_path
        from requirement.graph.infrastructure.logger import debug, info, warn, error, result
        # Removed imports for deleted modules (query_validator, versioned_cypher_executor)

        info("rgl.main", "Starting main function")

        db_path = get_db_path()
        if isinstance(db_path, dict) and db_path.get("type") == "EnvironmentConfigError":
            error("rgl.main", f"Environment configuration error: {db_path['message']}")
            sys.exit(1)

        # Check if database is initialized
        db_initialized = _check_db_initialized(db_path)
        if not db_initialized:
            info("rgl.main", "Database not found. Initializing database with schema...", db_path=db_path)
            from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
            
            try:
                success = apply_ddl_schema(db_path, create_test_data=False)
                if success:
                    info("rgl.main", "Database initialized successfully")
                else:
                    error("rgl.main", "Failed to initialize database: Schema application was unsuccessful.\n\nTroubleshooting steps:\n1. Check database permissions (write access to directory)\n2. Ensure sufficient disk space\n3. Verify KuzuDB installation\n4. Try manually: python -m requirement.graph.infrastructure.apply_ddl_schema")
                    sys.exit(1)
            except Exception as init_error:
                error("rgl.main", f"Database initialization failed: Unable to create or connect to the database.\n\nCommon causes:\n1. Database file is locked by another process\n2. Insufficient permissions to create database files\n3. Corrupted database - try deleting and re-initializing\n4. Missing KuzuDB dependencies\n\nError details: {str(init_error)}")
                sys.exit(1)

        # JSON形式の処理
        input_data = json.load(sys.stdin)
        input_type = input_data.get("type", "cypher")

        if input_type == "schema":
            # スキーマ管理
            action = input_data.get("action", "apply")
            if action == "apply":
                from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
                info("rgl.main", "Applying DDL schema", action=action)
                apply_ddl_schema(db_path, input_data.get("create_test_data", False))
                result({"status": "success", "message": "Schema applied"})
            else:
                error("Unknown schema action", details={"action": action})

        elif input_type == "template":
            # テンプレート処理
            from requirement.graph.application.template_processor import process_template
            from requirement.graph.application.search_adapter import SearchAdapter

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
                    warn("rgl.main", f"Search service initialization failed: Vector search is not available.\n\nThis is usually not critical - basic functionality will work without search.\n\nTo enable full search features:\n1. Check if the search database is properly initialized\n2. Verify vector search dependencies are installed\n3. Ensure sufficient disk space for search indexes\n\nError details: {e}")
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
            error("Unknown input type: This system accepts 'schema' or 'template' inputs.\n\nExample usage:\n- Schema: echo '{\"type\": \"schema\", \"action\": \"apply\"}' | python -m requirement.graph.main\n- Template: echo '{\"type\": \"template\", \"template\": \"create_requirement\", \"parameters\": {...}}' | python -m requirement.graph.main\n\nSee README.md for more examples.", details={"type": input_type, "supported_types": ["schema", "template"]})

        # クローズ処理は不要（KuzuDBは自動的にクローズされる）

    except json.JSONDecodeError as e:
        # JSONパースエラー
        error("Invalid JSON input: The system expects valid JSON data via stdin.\n\nCommon fixes:\n1. Check your JSON syntax (missing quotes, commas, brackets)\n2. Use proper escaping for special characters\n3. Test your JSON with: echo 'your_json' | python -m json.tool\n\nExample valid input:\necho '{\"type\": \"schema\", \"action\": \"apply\"}' | python -m requirement.graph.main", details={"error": str(e), "example": "{\"type\": \"schema\", \"action\": \"apply\"}"})
    except ImportError as e:
        # インポートエラー
        emergency_error("Module import failed: The required dependencies are not properly installed or accessible.\n\nTo fix this issue:\n1. Ensure you're in the correct Python environment (run 'nix develop' if using Nix)\n2. Install dependencies: pip install -r requirements.txt\n3. Check your PYTHONPATH includes the project root\n4. Verify the database is initialized: python -m requirement.graph.main <<< '{\"type\": \"schema\", \"action\": \"apply\"}'\n\nFor more help, see the setup instructions in README.md", details={"error": str(e), "fix_steps": ["nix develop", "pip install -r requirements.txt", "check PYTHONPATH", "initialize database"]})
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
        import sys
        sys.stdout.write(json.dumps({
            "type": "error",
            "level": "error",
            "message": "Unexpected system error: An unhandled error occurred in the main process.\n\nThis may indicate:\n1. A system-level issue (out of memory, disk full)\n2. A programming error that needs developer attention\n3. An interrupted process (Ctrl+C)\n\nPlease report this error with the details below if it persists.",
            "details": {"error": str(e), "error_type": type(e).__name__, "contact": "See README.md for issue reporting"}
        }, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
