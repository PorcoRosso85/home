"""
バージョニング対応Cypherエグゼキュータ
依存: version_service, kuzu_repository
"""
import re
from typing import Dict, Optional, Tuple
from ..application.version_service import create_version_service


def create_versioned_cypher_executor(repository: Dict) -> Dict:
    """
    バージョニング対応のCypherエグゼキュータを作成

    Args:
        repository: KuzuDBリポジトリ

    Returns:
        エグゼキュータ関数の辞書
    """

    # バージョンサービスを作成
    version_service = create_version_service(repository)

    def parse_create_query(query: str) -> Optional[Dict]:
        """CREATE文から要件情報を抽出"""
        # CREATE (r:RequirementEntity {...}) パターンを探す
        pattern = r'CREATE\s*\(\s*\w+:RequirementEntity\s*{([^}]+)}\s*\)'
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        # プロパティ部分を抽出
        props_str = match.group(1)

        # プロパティをパース（簡易実装）
        props = {}
        for prop in props_str.split(','):
            if ':' in prop:
                key, value = prop.split(':', 1)
                key = key.strip().strip("'\"")
                value = value.strip()

                # 数値の場合は数値として解析
                if value.isdigit():
                    props[key] = int(value)
                elif value.lower() in ['true', 'false']:
                    props[key] = value.lower() == 'true'
                else:
                    # 文字列の場合は引用符を削除
                    props[key] = value.strip("'\"")


        return props

    def parse_update_query(query: str) -> Optional[Tuple[str, Dict]]:
        """UPDATE文から要件IDと更新内容を抽出"""
        # MATCH ... SET パターンを探す
        match_pattern = r'MATCH\s*\(\s*\w+:RequirementEntity\s*{id:\s*[\'"]([^\'\"]+)[\'"]\s*}\s*\)'
        id_match = re.search(match_pattern, query, re.IGNORECASE)

        if not id_match:
            return None

        req_id = id_match.group(1)

        # SET部分をパース
        set_pattern = r'SET\s+(.+?)(?:RETURN|$)'
        set_match = re.search(set_pattern, query, re.IGNORECASE | re.DOTALL)

        if not set_match:
            return None

        # 更新内容をパース（簡易実装）
        updates = {"id": req_id}
        set_str = set_match.group(1)

        # プロパティ更新を抽出
        prop_pattern = r'\w+\.(\w+)\s*=\s*[\'"]([^\'\"]+)[\'"]'
        for match in re.finditer(prop_pattern, set_str):
            prop_name = match.group(1)
            prop_value = match.group(2)
            updates[prop_name] = prop_value

        return req_id, updates

    def extract_metadata(input_data: Dict) -> Dict[str, str]:
        """入力データからメタデータを抽出"""
        metadata = input_data.get("metadata", {})
        return {
            "author": metadata.get("author", "system"),
            "reason": metadata.get("reason", "")
        }

    def execute_versioned_query(input_data: Dict) -> Dict:
        """
        バージョニング対応でクエリを実行

        Args:
            input_data: クエリとメタデータを含む入力

        Returns:
            実行結果
        """
        query = input_data.get("query", "")
        metadata = extract_metadata(input_data)

        # CREATE操作の検出
        if "CREATE" in query.upper() and "REQUIREMENTENTITY" in query.upper():
            props = parse_create_query(query)
            if props and "id" in props and "title" in props:
                # バージョニング付きで作成
                props.update(metadata)
                try:
                    result = version_service["create_versioned_requirement"](props)

                    # 結果を整形
                    return {
                        "status": "success",
                        "data": [[
                            result["entity_id"],
                            result["version_id"],
                            result["version"],
                            result["created_at"]
                        ]],
                        "metadata": {
                            "version": result["version"],
                            "version_id": result["version_id"],
                            "location_uri": result["location_uri"]
                        }
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                        "message": f"Failed to create versioned requirement: {str(e)}"
                    }

        # UPDATE操作の検出
        if "MATCH" in query.upper() and "SET" in query.upper():
            update_info = parse_update_query(query)
            if update_info:
                req_id, updates = update_info
                updates.update(metadata)

                # バージョニング付きで更新
                result = version_service["update_versioned_requirement"](updates)

                # 結果を整形
                return {
                    "status": "success",
                    "data": [[
                        result["entity_id"],
                        result["version_id"],
                        result["version"],
                        result["updated_at"]
                    ]],
                    "metadata": {
                        "version": result["version"],
                        "previous_version": result["previous_version"],
                        "version_id": result["version_id"],
                        "change_reason": result["change_reason"],
                        "author": result["author"]
                    }
                }

        # 履歴取得クエリの検出
        if "RETURN" in query.upper() and ".history" in query:
            history_pattern = r'\{id:\s*[\'"]([^\'\"]+)[\'"]\s*}\s*\)\s*RETURN\s+\w+\.history'
            match = re.search(history_pattern, query, re.IGNORECASE)
            if match:
                req_id = match.group(1)
                history = version_service["get_requirement_history"](req_id)
                return {
                    "status": "success",
                    "data": {"history": history}
                }

        # タイムスタンプ指定の取得
        if "at_timestamp" in query:
            at_pattern = r'\{id:\s*[\'"]([^\'\"]+)[\'"]\s*}\s*\)\s*RETURN\s+\w+\.at_timestamp\([\'"]([^\'\"]+)[\'"]\)'
            match = re.search(at_pattern, query, re.IGNORECASE)
            if match:
                req_id = match.group(1)
                timestamp = match.group(2)
                state = version_service["get_requirement_at_timestamp"](req_id, timestamp)
                return {
                    "status": "success",
                    "data": state
                }

        # 差分取得クエリの検出
        if ".diff" in query:
            diff_pattern = r'\{id:\s*[\'"]([^\'\"]+)[\'"]\s*}\s*\)\s*RETURN\s+\w+\.diff\((\d+),\s*(\d+)\)'
            match = re.search(diff_pattern, query, re.IGNORECASE)
            if match:
                req_id = match.group(1)
                from_version = int(match.group(2))
                to_version = int(match.group(3))
                diff = version_service["get_version_diff"](req_id, from_version, to_version)
                return {
                    "status": "success",
                    "data": {"diff": diff}
                }

        # その他のクエリは通常実行
        result = repository["execute"](query, {})
        data = []
        while result.has_next():
            data.append(result.get_next())

        return {
            "status": "success",
            "data": data
        }

    return {
        "execute": execute_versioned_query
    }
