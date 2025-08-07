"""
Requirement Graph - 要件管理CLI

使い方:
    # CLI形式
    python -m requirement.graph.main init
    python -m requirement.graph.main add
    python -m requirement.graph.main search "検索クエリ"
    
    # JSON形式（後方互換）
    echo '{"type": "schema", "action": "apply"}' | python -m requirement.graph.main
    echo '{"type": "template", "template": "create_requirement"}' | python -m requirement.graph.main

戻り値:
    {"status": "success|error", "message": "..."}
"""
import sys
import json
import argparse


def handle_cli_command(db_path: str):
    """CLIコマンドを処理する"""
    from requirement.graph.infrastructure.logger import info, error, result
    
    parser = argparse.ArgumentParser(
        prog='requirement-graph',
        description='要件管理システム'
    )
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # initコマンド
    init_parser = subparsers.add_parser('init', help='データベースを初期化')
    init_parser.add_argument('--with-test-data', action='store_true', 
                            help='テストデータも作成する')
    
    # addコマンド
    add_parser = subparsers.add_parser('add', help='要件を追加')
    add_parser.add_argument('--id', type=str, help='要件ID')
    add_parser.add_argument('--title', type=str, help='要件タイトル')
    add_parser.add_argument('--description', type=str, help='要件説明')
    
    # searchコマンド
    search_parser = subparsers.add_parser('search', help='要件を検索')
    search_parser.add_argument('query', type=str, help='検索クエリ')
    search_parser.add_argument('--limit', type=int, default=10, help='検索結果の上限')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        handle_init_command(db_path, args.with_test_data)
    elif args.command == 'add':
        handle_add_command(db_path, args)
    elif args.command == 'search':
        handle_search_command(db_path, args)
    else:
        parser.print_help()
        error("Unknown command", details={"command": args.command if args.command else "None"})


def handle_init_command(db_path: str, with_test_data: bool = False):
    """initコマンドの処理"""
    from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
    from requirement.graph.infrastructure.logger import info, result
    import os
    
    info("rgl.init", "Initializing database", db_path=db_path)
    
    # データベースが既に存在するかチェック
    if os.path.exists(db_path) and os.path.exists(os.path.join(db_path, "catalog.kz")):
        result({
            "status": "info",
            "message": f"データベースは既に存在します: {db_path}",
            "details": "再初期化する場合は、データベースディレクトリを削除してから実行してください"
        })
        return
    
    # スキーマ適用
    apply_ddl_schema(db_path, with_test_data)
    result({
        "status": "success",
        "message": "データベースを初期化しました",
        "db_path": db_path,
        "test_data": with_test_data
    })


def handle_add_command(db_path: str, args):
    """addコマンドの処理"""
    from requirement.graph.infrastructure.logger import info, result, error
    
    # 対話的入力
    if not args.id:
        args.id = input("要件ID: ")
    if not args.title:
        args.title = input("要件タイトル: ")
    if not args.description:
        args.description = input("要件説明: ")
    
    if not all([args.id, args.title, args.description]):
        error("すべてのフィールドが必要です", details={
            "missing": [f for f, v in [("id", args.id), ("title", args.title), ("description", args.description)] if not v]
        })
        return
    
    info("rgl.add", "Adding requirement", id=args.id, title=args.title)
    
    try:
        # 重複チェックと要件作成
        from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
        from requirement.graph.application.template_processor import process_template
        
        repository = create_kuzu_repository(db_path)
        
        # 重複チェック
        duplicate_check_data = {
            "type": "template",
            "template": "find_requirement",
            "parameters": {
                "id": args.id
            }
        }
        
        check_result = process_template(duplicate_check_data, repository, None)
        
        if check_result and check_result.get("results"):
            error("要件IDが既に存在します", details={
                "id": args.id,
                "existing": check_result["results"][0] if check_result["results"] else None
            })
            return
        
        # 要件作成
        create_data = {
            "type": "template",
            "template": "create_requirement",
            "parameters": {
                "id": args.id,
                "title": args.title,
                "description": args.description
            }
        }
        
        create_result = process_template(create_data, repository, None)
        
        if "error" in create_result:
            error("要件の作成に失敗しました", details=create_result)
        else:
            result({
                "status": "success",
                "message": "要件を作成しました",
                "requirement": {
                    "id": args.id,
                    "title": args.title,
                    "description": args.description
                }
            })
            
    except Exception as e:
        error("要件作成中にエラーが発生しました", details={"error": str(e)})


def handle_search_command(db_path: str, args):
    """searchコマンドの処理"""
    from requirement.graph.infrastructure.logger import info, result, error
    
    info("rgl.search", "Searching requirements", query=args.query, limit=args.limit)
    
    try:
        from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
        from requirement.graph.application.template_processor import process_template
        
        repository = create_kuzu_repository(db_path)
        
        # 検索実行
        search_data = {
            "type": "template",
            "template": "list_requirements",
            "parameters": {
                "limit": args.limit
            }
        }
        
        search_result = process_template(search_data, repository, None)
        
        if "error" in search_result:
            error("検索に失敗しました", details=search_result)
        else:
            # 検索クエリでフィルタリング（簡単なマッチング）
            results = search_result.get("results", [])
            if args.query and results:
                filtered_results = []
                query_lower = args.query.lower()
                for req in results:
                    if (query_lower in req.get("title", "").lower() or
                        query_lower in req.get("description", "").lower() or
                        query_lower in req.get("id", "").lower()):
                        filtered_results.append(req)
                results = filtered_results
            
            result({
                "status": "success",
                "message": f"{len(results)}件の要件が見つかりました",
                "query": args.query,
                "results": results[:args.limit]
            })
            
    except Exception as e:
        error("検索中にエラーが発生しました", details={"error": str(e)})


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

        # CLIコマンドの処理
        if len(sys.argv) > 1:
            handle_cli_command(db_path)
            return

        # JSON形式の処理（後方互換）
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
        import sys
        sys.stdout.write(json.dumps({
            "type": "error",
            "level": "error",
            "message": "Unexpected error in main()",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
