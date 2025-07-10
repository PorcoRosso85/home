"""
Query Validator - Cypherクエリのセキュリティチェック
依存: なし
外部依存: なし
"""
from typing import Dict, Optional, Tuple
import re


class QueryValidator:
    """
    LLMから受け取ったCypherクエリの安全性を検証
    """

    # 許可するCypherキーワード
    ALLOWED_KEYWORDS = {
        "MATCH", "CREATE", "SET", "DELETE", "RETURN", "WHERE",
        "WITH", "ORDER", "BY", "LIMIT", "SKIP", "UNION", "CALL", "YIELD",
        "AND", "OR", "NOT", "EXISTS", "AS", "DISTINCT", "COUNT", "SUM",
        "AVG", "MIN", "MAX", "COLLECT", "CONTAINS", "STARTS", "ENDS"
    }

    # 禁止するパターン
    FORBIDDEN_PATTERNS = [
        r"DROP\s+(DATABASE|TABLE|INDEX)",
        r"DETACH\s+DELETE",
        r"REMOVE\s+.*\.\*",  # すべてのプロパティ削除
        r"SET\s+.*\s*=\s*\{\}",  # 空オブジェクトへの置換
    ]

    # 許可するノードラベル
    ALLOWED_LABELS = {
        "RequirementEntity", "LocationURI", "VersionState",
        "CodeEntity", "ReferenceEntity",
        "ConfigurationEntity", "ImplementationGuideEntity",
        "EntityAggregationView"
    }

    # 許可する関係タイプ
    ALLOWED_RELATIONSHIPS = {
        "DEPENDS_ON", "PARENT_OF", "LOCATES", "LOCATES_CODE",
        "FOLLOWS", "TRACKS_STATE_OF", "CONTAINS_LOCATION",
        "HAS_VERSION", "HAS_VERSION_CODE", "IS_IMPLEMENTED_BY",
        "IS_VERIFIED_BY", "REFERS_TO", "REFERENCES_CODE",
        "TESTS", "CONTAINS_CODE", "CONFIGURES", "GUIDES",
        "USES", "AGGREGATES_REQ", "AGGREGATES_CODE"
    }

    def validate(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        クエリの安全性を検証

        Args:
            query: 検証するCypherクエリ

        Returns:
            (is_valid, error_message)
        """
        # 空クエリチェック
        if not query or not query.strip():
            return False, "Query cannot be empty"

        # 大文字変換して検証
        query_upper = query.upper()

        # 禁止パターンのチェック
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"

        # DROP, DETACH DELETEの単純チェック
        if "DROP" in query_upper and ("DATABASE" in query_upper or "TABLE" in query_upper):
            return False, "DROP DATABASE/TABLE is not allowed"

        if "DETACH" in query_upper and "DELETE" in query_upper:
            return False, "DETACH DELETE is not allowed"

        # パラメータインジェクションの検出
        if ";" in query and not re.match(r"^[^'\"]*;[^'\"]*$", query):
            # セミコロンが文字列リテラル外にある場合
            if re.search(r"(DROP|DELETE|DETACH|REMOVE)\s", query_upper):
                return False, "Potential injection attempt detected"

        # ラベルの検証（ノードラベルのみ、関係タイプは除外）
        # ノードラベルは (x:Label) または (:Label) の形式
        label_pattern = r"\([\w\s]*:(\w+)[\w\s]*\)"
        found_labels = re.findall(label_pattern, query)
        for label in found_labels:
            if label not in self.ALLOWED_LABELS:
                return False, f"Unauthorized label: {label}"

        # 関係タイプの検証
        rel_pattern = r"\[:\s*(\w+)\s*\]"
        found_rels = re.findall(rel_pattern, query)
        for rel in found_rels:
            if rel not in self.ALLOWED_RELATIONSHIPS:
                # カスタムプロシージャ呼び出しは許可
                if not query_upper.startswith("CALL"):
                    return False, f"Unauthorized relationship: {rel}"

        return True, None

    def sanitize_parameters(self, parameters: Dict) -> Dict:
        """
        パラメータのサニタイズ

        Args:
            parameters: クエリパラメータ

        Returns:
            サニタイズされたパラメータ
        """
        if not parameters:
            return {}

        sanitized = {}

        # 危険な文字列パターン
        dangerous_patterns = [
            r";\s*(DROP|DELETE|DETACH|REMOVE)",
            r"--",  # SQLコメント
            r"/\*.*\*/",  # ブロックコメント
            r"(DROP|DELETE)\s+(DATABASE|TABLE)",
        ]

        for key, value in parameters.items():
            if isinstance(value, str):
                # 危険なパターンを除去
                clean_value = value
                for pattern in dangerous_patterns:
                    clean_value = re.sub(pattern, "", clean_value, flags=re.IGNORECASE)

                # セミコロンを安全な文字に置換
                clean_value = clean_value.replace(";", "")

                sanitized[key] = clean_value
            else:
                # 文字列以外はそのまま
                sanitized[key] = value

        return sanitized
