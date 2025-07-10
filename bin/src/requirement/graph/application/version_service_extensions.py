"""
Version Service Extensions - DQLテンプレートを使用する追加機能

既存のversion_service.pyを拡張し、新しいDQLテンプレートを使用する機能を提供
"""
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_template(category: str, name: str) -> str:
    """Cypherテンプレートを読み込む"""
    template_path = Path(__file__).parent.parent / "query" / category / f"{name}.cypher"
    if template_path.exists():
        return template_path.read_text()
    else:
        raise FileNotFoundError(f"Template not found: {template_path}")


def list_all_versions(repository: Dict[str, Any], req_id: str) -> List[Dict[str, Any]]:
    """
    要件の全バージョン一覧を取得

    Args:
        repository: リポジトリインスタンス
        req_id: 要件ID

    Returns:
        バージョン一覧
    """
    template = load_template("dql", "list_all_versions")
    result = repository["execute"](template, {"req_id": req_id})

    versions = []
    version_num = 1

    while result.has_next():
        row = result.get_next()
        versions.append({
            "version": version_num,
            "version_id": row[0],
            "operation": row[1],
            "timestamp": row[2],
            "author": row[3]
        })
        version_num += 1

    return versions


def get_version_diff_from_template(repository: Dict[str, Any], req_id: str,
                                  from_version: int, to_version: int) -> Optional[Dict[str, Any]]:
    """
    DQLテンプレートを使用してバージョン差分を取得

    Args:
        repository: リポジトリインスタンス
        req_id: 要件ID
        from_version: 比較元バージョン番号
        to_version: 比較先バージョン番号

    Returns:
        差分情報（テンプレートベース）
    """
    template = load_template("dql", "get_version_diff")
    result = repository["execute"](template, {
        "req_id": req_id,
        "from_version": from_version,
        "to_version": to_version
    })

    if result.has_next():
        row = result.get_next()
        version_data = row[0]

        # 差分を計算
        from_v = version_data.get("from_version", {})
        to_v = version_data.get("to_version", {})

        if from_v and to_v:
            changed_fields = []
            old_values = {}
            new_values = {}

            # フィールドごとに比較
            for field in ["title", "description", "status", "priority"]:
                if from_v.get(field) != to_v.get(field):
                    changed_fields.append(field)
                    old_values[field] = from_v.get(field)
                    new_values[field] = to_v.get(field)

            return {
                "req_id": req_id,
                "from_version": from_version,
                "to_version": to_version,
                "changed_fields": changed_fields,
                "old_values": old_values,
                "new_values": new_values,
                "change_reason": to_v.get("change_reason"),
                "author": to_v.get("author"),
                "timestamp": to_v.get("timestamp")
            }

    return None
