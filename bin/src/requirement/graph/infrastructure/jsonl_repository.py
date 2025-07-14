"""
JSONL Repository - JSONL形式での永続化
依存: domain, application
外部依存: os, json
"""
import os
import json
from typing import List, Dict
from datetime import datetime


def create_jsonl_repository(file_path: str) -> Dict:
    """
    JSONLベースのリポジトリを作成

    Args:
        file_path: JSONLファイルのパス

    Returns:
        Repository関数の辞書
    """

    def ensure_file_exists():
        """ファイルが存在しない場合は作成"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, 'w'):
                pass

    def save(decision: Decision) -> DecisionResult:
        """決定事項を保存（既存の場合は更新）"""
        ensure_file_exists()

        # 既存のレコードをチェック
        existing = find(decision["id"])
        if "type" not in existing or existing.get("type") != "DecisionNotFoundError":
            # 既存レコードがある場合は更新
            return update(decision)

        # datetime → ISO形式文字列に変換
        save_data = decision.copy()
        if isinstance(save_data.get("created_at"), datetime):
            save_data["created_at"] = save_data["created_at"].isoformat()

        # 追記モードで保存
        with open(file_path, 'a') as f:
            json.dump(save_data, f, ensure_ascii=False)
            f.write('\n')

        return decision

    def find(decision_id: str) -> DecisionResult:
        """IDで決定事項を検索"""
        ensure_file_exists()

        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get("id") == decision_id:
                        # ISO形式 → datetimeに変換
                        if "created_at" in data and isinstance(data["created_at"], str):
                            data["created_at"] = datetime.fromisoformat(data["created_at"])
                        return data

        return {
            "type": "DecisionNotFoundError",
            "message": f"Decision {decision_id} not found",
            "decision_id": decision_id
        }

    def find_all() -> List[Decision]:
        """全ての決定事項を取得"""
        ensure_file_exists()

        decisions = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # ISO形式 → datetimeに変換
                    if "created_at" in data and isinstance(data["created_at"], str):
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                    decisions.append(data)

        return decisions

    def update(decision: Decision) -> DecisionResult:
        """決定事項を更新（全体を書き換え）"""
        ensure_file_exists()

        all_decisions = find_all()
        updated = False

        for i, d in enumerate(all_decisions):
            if d["id"] == decision["id"]:
                all_decisions[i] = decision
                updated = True
                break

        if not updated:
            return {
                "type": "DecisionNotFoundError",
                "message": f"Decision {decision['id']} not found",
                "decision_id": decision["id"]
            }

        # ファイル全体を書き直し
        with open(file_path, 'w') as f:
            for d in all_decisions:
                save_data = d.copy()
                if isinstance(save_data.get("created_at"), datetime):
                    save_data["created_at"] = save_data["created_at"].isoformat()
                json.dump(save_data, f, ensure_ascii=False)
                f.write('\n')

        return decision

    return {
        "save": save,
        "find": find,
        "find_all": find_all,
        "update": update
    }
