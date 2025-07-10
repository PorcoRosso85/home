"""
エラーハンドラー（アプリケーション層）

技術的なエラーをユーザーフレンドリーなメッセージに変換
"""
from typing import Dict, Any
from datetime import datetime
from domain.error_types import UserFriendlyError, ErrorExample, RecoveryGuidance


def create_error_handler() -> Dict[str, Any]:
    """
    エラーハンドラーを作成

    Returns:
        エラーハンドリング関数の辞書
    """

    def handle_dependency_creation_error(original_error: str, query: str) -> UserFriendlyError:
        """依存関係作成エラーをハンドル"""
        if "Variable node is not in scope" in original_error:
            return UserFriendlyError(
                error_code="INVALID_DEPENDENCY_SYNTAX",
                user_message="依存関係の作成に失敗しました：クエリの構文が正しくありません",
                explanation="KuzuDBでは、既存ノード間のリレーション作成時に別の構文が必要です",
                suggested_action="以下のいずれかの方法を試してください",
                examples=[
                    ErrorExample(
                        description="推奨：既存ノード間のリレーション作成",
                        query='MATCH (a:RequirementEntity) WHERE a.id = "req_tm_003" MATCH (b:RequirementEntity) WHERE b.id = "req_tm_002" CREATE (a)-[:DEPENDS_ON]->(b)'
                    ),
                    ErrorExample(
                        description="代替：CREATE構文を使用（事前チェック付き）",
                        query='MATCH (a:RequirementEntity {id: "req_tm_003"}) MATCH (b:RequirementEntity {id: "req_tm_002"}) WHERE NOT EXISTS { (a)-[:DEPENDS_ON]->(b) } CREATE (a)-[:DEPENDS_ON]->(b)'
                    )
                ],
                technical_details={
                    "original_error": original_error,
                    "context": "KuzuDB requires separate MATCH clauses for binding variables"
                },
                timestamp=datetime.now().isoformat()
            )

        # その他の依存関係エラー
        return UserFriendlyError(
            error_code="DEPENDENCY_ERROR",
            user_message="依存関係の作成に失敗しました",
            explanation="クエリの実行中にエラーが発生しました",
            suggested_action="クエリの構文を確認してください",
            examples=[],
            technical_details={"original_error": original_error},
            timestamp=datetime.now().isoformat()
        )

    def handle_schema_error(original_error: str) -> Dict[str, Any]:
        """スキーマエラーをハンドル"""
        recovery = None

        if "Failed to apply schema" in original_error:
            recovery = RecoveryGuidance(
                error_type="SCHEMA_INIT_FAILED",
                steps=[
                    "1. 既存のデータベースディレクトリを確認: ls -la ./rgl_db",
                    "2. 必要に応じてバックアップ: cp -r ./rgl_db ./rgl_db.backup",
                    "3. クリーンな状態から再開: rm -rf ./rgl_db && nix run .#schema",
                    "4. それでも失敗する場合は、権限を確認: ls -la | grep rgl_db"
                ]
            )
        elif "Permission denied" in original_error:
            recovery = RecoveryGuidance(
                error_type="PERMISSION_DENIED",
                steps=[
                    "1. ディレクトリの権限を確認: ls -la ./rgl_db",
                    "2. 書き込み権限を付与: chmod 755 ./rgl_db",
                    "3. 再実行: nix run .#schema"
                ]
            )

        error_dict = {
            "type": "error",
            "level": "error",
            "message": "スキーマ初期化に失敗しました",
            "score": -1.0,
            "timestamp": datetime.now().isoformat()
        }

        if recovery:
            error_dict.update(recovery.to_dict())

        return error_dict

    def handle_kuzu_import_error(original_error: str) -> Dict[str, Any]:
        """KuzuDBインポートエラーをハンドル"""
        return {
            "type": "environment_setup",
            "level": "error",
            "error_code": "LIBRARY_SETUP",
            "user_message": "KuzuDBライブラリのロードに失敗しました",
            "guidance": {
                "issue": "KuzuDBライブラリのロードに失敗しました",
                "possible_causes": [
                    "LD_LIBRARY_PATHが未設定",
                    "kuzu Pythonパッケージが未インストール"
                ],
                "setup_commands": [
                    "nix develop  # 推奨: 必要な環境を自動設定",
                    "# または手動で:",
                    "export LD_LIBRARY_PATH=/nix/store/.../gcc-.../lib/"
                ],
                "next_action": "nix develop環境で実行してください"
            },
            "timestamp": datetime.now().isoformat()
        }

    def handle_environment_error(error_type: str, missing_vars: list = None) -> Dict[str, Any]:
        """環境変数エラーをハンドル"""
        if error_type == "RGL_DB_PATH_NOT_SET":
            return {
                "type": "environment_setup",
                "level": "error",
                "error_code": "ENV_VAR_MISSING",
                "user_message": "必要な環境変数が設定されていません",
                "guidance": {
                    "missing": ["RGL_DB_PATH"],
                    "setup_commands": [
                        "export RGL_DB_PATH=./rgl_db",
                        "# または",
                        "nix develop  # 推奨: 自動的に設定されます"
                    ],
                    "next_action": "環境変数を設定してから再実行してください"
                },
                "timestamp": datetime.now().isoformat()
            }

        return {
            "type": "error",
            "level": "error",
            "message": f"環境エラー: {error_type}",
            "timestamp": datetime.now().isoformat()
        }

    return {
        "handle_dependency_creation_error": handle_dependency_creation_error,
        "handle_schema_error": handle_schema_error,
        "handle_kuzu_import_error": handle_kuzu_import_error,
        "handle_environment_error": handle_environment_error
    }
