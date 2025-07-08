"""
ユーザー体験改善のための統合テスト

これらのテストは、RGLシステムのユーザビリティ向上のための仕様を検証する。
環境構築、エラーメッセージ、対話性の改善に焦点を当てた「実行可能な仕様書」である。

テスト対象:
- 環境設定ヘルパー: 環境変数の検証とガイダンス機能
- エラーメッセージ改善: アクション可能なエラーメッセージ生成
- 状態確認API: 現在の要件グラフ状態を取得する機能
- ヘルプシステム: コマンドヘルプとサンプル提供機能

テスト手法:
- テーブル駆動テスト（TDT）: 様々なユーザーシナリオを網羅的に検証
"""
from typing import Dict, List, Any


class TestEnvironmentSetupHelper:
    """環境設定ヘルパーのテスト - テーブル駆動テスト"""
    
    def test_環境変数未設定時に必要な設定を案内する(self):
        """環境変数が未設定の場合、設定方法を含む明確なメッセージを返す"""
        # テーブル駆動テスト: 環境変数の状態と期待されるガイダンス
        test_cases = [
            {
                "name": "RGL_DB_PATH未設定",
                "env_vars": {},
                "expected_error_type": "environment_setup",
                "expected_guidance": {
                    "missing": ["RGL_DB_PATH"],
                    "setup_commands": [
                        "export RGL_DB_PATH=./rgl_db",
                        "# または",
                        "nix develop  # 推奨: 自動的に設定されます"
                    ],
                    "next_action": "環境変数を設定してから再実行してください"
                }
            },
            {
                "name": "LD_LIBRARY_PATH未設定（kuzu import失敗時）",
                "env_vars": {"RGL_DB_PATH": "./rgl_db"},
                "import_error": "module 'kuzu' has no attribute 'Database'",
                "expected_error_type": "library_setup",
                "expected_guidance": {
                    "issue": "KuzuDBライブラリのロードに失敗しました",
                    "possible_causes": [
                        "LD_LIBRARY_PATHが未設定",
                        "kuzu Pythonパッケージが未インストール"
                    ],
                    "setup_commands": [
                        "nix develop  # 推奨: 必要な環境を自動設定",
                        "# または手動で:",
                        "export LD_LIBRARY_PATH=/nix/store/.../gcc-.../lib/"
                    ]
                }
            },
            {
                "name": "スキーマ未初期化",
                "env_vars": {"RGL_DB_PATH": "./rgl_db"},
                "db_error": "Table RequirementEntity does not exist",
                "expected_error_type": "schema_setup",
                "expected_guidance": {
                    "issue": "データベーススキーマが初期化されていません",
                    "setup_commands": [
                        "nix run .#schema  # スキーマを初期化",
                        "# エラーが続く場合:",
                        "rm -rf ./rgl_db  # DBをリセット",
                        "nix run .#schema  # 再初期化"
                    ],
                    "next_action": "スキーマ初期化後、要件の作成を再試行してください"
                }
            }
        ]
        
        # 仕様: 各エラーケースで適切なガイダンスが提供される
        for case in test_cases:
            # ここでは仕様のみを定義（実装は後で行う）
            pass


class TestErrorMessageImprovement:
    """エラーメッセージ改善のテスト - テーブル駆動テスト"""
    
    def test_エラー時に次のアクションを明示する(self):
        """エラーメッセージは問題の説明と解決策を含む"""
        test_cases = [
            {
                "name": "循環参照検出",
                "error": {
                    "type": "circular_reference",
                    "cycle": ["req_001", "req_002", "req_003", "req_001"]
                },
                "expected_message_structure": {
                    "problem": "循環参照が検出されました",
                    "details": "req_001 → req_002 → req_003 → req_001",
                    "impact": "このままでは要件の実装順序が決定できません",
                    "suggested_actions": [
                        "依存関係を見直して循環を解消してください",
                        "例: req_003 → req_001 の依存を削除"
                    ],
                    "query_examples": [
                        'MATCH (:RequirementEntity {id: "req_003"})-[r:DEPENDS_ON]->(:RequirementEntity {id: "req_001"}) DELETE r'
                    ]
                }
            },
            {
                "name": "曖昧な要件",
                "friction": {
                    "type": "ambiguity_friction",
                    "requirement": "使いやすいECサイト",
                    "score": -0.6
                },
                "expected_message_structure": {
                    "problem": "要件が曖昧です",
                    "details": "「使いやすい」という表現は解釈が分かれます",
                    "suggested_actions": [
                        "具体的な受け入れ基準を追加してください",
                        "例: レスポンス時間、クリック数、エラー率など"
                    ],
                    "query_examples": [
                        'CREATE (r:RequirementEntity {id: "req_ec_002", title: "3秒以内のページ読み込み", parent_id: "req_ec_001"})'
                    ]
                }
            }
        ]
        
        # 仕様: エラーメッセージは構造化され、次のアクションが明確
        pass


class TestStateQueryAPI:
    """状態確認APIのテスト - テーブル駆動テスト"""
    
    def test_現在の要件グラフ状態を確認できる(self):
        """様々なクエリタイプで現在の状態を取得"""
        test_cases = [
            {
                "name": "全要件の一覧取得",
                "query_type": "list_requirements",
                "expected_response": {
                    "type": "requirements_list",
                    "count": "number",
                    "requirements": [
                        {
                            "id": "string",
                            "title": "string",
                            "priority": "number",
                            "depth": "number",
                            "children_count": "number",
                            "dependencies_count": "number"
                        }
                    ],
                    "summary": {
                        "total": "number",
                        "by_priority": {"1": "number", "2": "number", "...": "..."},
                        "max_depth": "number",
                        "health": "string"
                    }
                }
            },
            {
                "name": "特定要件の詳細取得",
                "query_type": "get_requirement",
                "parameters": {"id": "req_001"},
                "expected_response": {
                    "type": "requirement_detail",
                    "requirement": {
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "priority": "number",
                        "created_at": "timestamp",
                        "updated_at": "timestamp"
                    },
                    "relationships": {
                        "parent": "requirement_id or null",
                        "children": ["requirement_ids"],
                        "depends_on": ["requirement_ids"],
                        "depended_by": ["requirement_ids"]
                    },
                    "health_check": {
                        "issues": ["issue_descriptions"],
                        "score": "number",
                        "recommendations": ["action_items"]
                    }
                }
            },
            {
                "name": "要件グラフの健全性チェック",
                "query_type": "health_check",
                "expected_response": {
                    "type": "health_report",
                    "overall_health": "healthy|needs_attention|critical",
                    "scores": {
                        "ambiguity": "number",
                        "priority": "number",
                        "structure": "number"
                    },
                    "issues": [
                        {
                            "type": "string",
                            "severity": "high|medium|low",
                            "affected_requirements": ["ids"],
                            "description": "string",
                            "suggested_fix": "string"
                        }
                    ],
                    "next_steps": ["prioritized_action_items"]
                }
            }
        ]
        
        # 仕様: 各クエリタイプで適切な状態情報が返される
        pass


class TestHelpSystem:
    """ヘルプシステムのテスト - テーブル駆動テスト"""
    
    def test_コンテキストに応じたヘルプを提供する(self):
        """ユーザーの状況に応じた適切なヘルプとサンプル"""
        test_cases = [
            {
                "name": "初回起動時のヘルプ",
                "context": {"requirements_count": 0, "first_run": True},
                "query_type": "help",
                "expected_help": {
                    "type": "getting_started",
                    "welcome_message": "RGLへようこそ！要件グラフの構築を始めましょう",
                    "quick_start": [
                        {
                            "step": 1,
                            "description": "最初の要件を作成",
                            "example_query": 'CREATE (r:RequirementEntity {id: "req_001", title: "プロジェクトのビジョン", description: "詳細な説明", priority: 5})',
                            "explanation": "最上位の要件（ビジョン）から始めることを推奨"
                        },
                        {
                            "step": 2,
                            "description": "子要件を追加",
                            "example_query": 'CREATE (r:RequirementEntity {id: "req_002", title: "機能要件", parent_id: "req_001", priority: 4})',
                            "explanation": "parent_idで親子関係を定義"
                        }
                    ],
                    "tips": [
                        "priority は 1（低）から 5（高）で設定",
                        "グラフの深さは最大5階層まで"
                    ]
                }
            },
            {
                "name": "エラー後のヘルプ",
                "context": {"last_error": "circular_reference"},
                "query_type": "help",
                "expected_help": {
                    "type": "error_recovery",
                    "error_context": "循環参照エラーからの回復",
                    "diagnostic_queries": [
                        {
                            "description": "循環を含む要件を特定",
                            "query": "MATCH path=(r:RequirementEntity)-[:DEPENDS_ON*]->(r) RETURN path"
                        },
                        {
                            "description": "依存関係を確認",
                            "query": 'MATCH (r:RequirementEntity {id: "問題のID"})-[:DEPENDS_ON]->(d) RETURN r.id, d.id'
                        }
                    ],
                    "fix_examples": [
                        {
                            "description": "依存関係を削除",
                            "query": 'MATCH (:RequirementEntity {id: "from_id"})-[rel:DEPENDS_ON]->(:RequirementEntity {id: "to_id"}) DELETE rel'
                        }
                    ]
                }
            },
            {
                "name": "クエリタイプ別ヘルプ",
                "query_type": "help",
                "parameters": {"topic": "queries"},
                "expected_help": {
                    "type": "query_reference",
                    "categories": {
                        "creation": {
                            "description": "要件の作成",
                            "examples": ["CREATE文の例"]
                        },
                        "modification": {
                            "description": "要件の更新",
                            "examples": ["MATCH-SET文の例"]
                        },
                        "query": {
                            "description": "要件の検索",
                            "examples": ["MATCH-RETURN文の例"]
                        },
                        "analysis": {
                            "description": "グラフ分析",
                            "examples": ["パス検索、集計クエリ"]
                        }
                    }
                }
            }
        ]
        
        # 仕様: コンテキストに応じた実用的なヘルプが提供される
        pass