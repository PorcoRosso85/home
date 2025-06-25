"""永続化アダプター - 決定事項をファイルに保存"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from ..domain.types import RequirementDict, ErrorDict


class FileBasedRepository:
    """ファイルベースの要件リポジトリ"""
    
    def __init__(self, file_path: str = None):
        """
        Args:
            file_path: 保存先ファイルパス（デフォルト: ~/.rgl/decisions.jsonl）
        """
        if file_path is None:
            home = Path.home()
            rgl_dir = home / ".rgl"
            rgl_dir.mkdir(exist_ok=True)
            self.file_path = rgl_dir / "decisions.jsonl"
        else:
            self.file_path = Path(file_path)
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # インメモリキャッシュ
        self._cache: Dict[str, RequirementDict] = {}
        self._load_from_file()
    
    def _load_from_file(self):
        """ファイルから既存の決定事項を読み込み"""
        if not self.file_path.exists():
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # 日時文字列をdatetimeに変換
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                        self._cache[data['id']] = data
        except Exception as e:
            print(f"警告: 既存データの読み込みエラー: {e}")
    
    def save(self, requirement: RequirementDict) -> str | ErrorDict:
        """要件を保存"""
        try:
            # キャッシュに保存
            self._cache[requirement['id']] = requirement
            
            # ファイルに追記（JSONLフォーマット）
            data_to_save = requirement.copy()
            # datetimeを文字列に変換
            data_to_save['created_at'] = requirement['created_at'].isoformat()
            data_to_save['updated_at'] = requirement['updated_at'].isoformat()
            # embeddingはシンプルに保存
            data_to_save['embedding'] = {
                'vector': requirement['embedding']['vector'],
                'model_name': requirement['embedding']['model_name'],
                'dimension': requirement['embedding']['dimension']
            }
            
            with open(self.file_path, 'a', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False)
                f.write('\n')
            
            return requirement['id']
            
        except Exception as e:
            return {"error": str(e), "code": "SAVE_ERROR", "details": None}
    
    def find_by_id(self, requirement_id: str) -> RequirementDict | ErrorDict:
        """IDで要件を検索"""
        if requirement_id in self._cache:
            return self._cache[requirement_id]
        return {"error": f"Requirement {requirement_id} not found", "code": "NOT_FOUND", "details": None}
    
    def find_similar(self, embedding: Dict, limit: int) -> List[RequirementDict] | ErrorDict:
        """類似要件を検索"""
        try:
            if not self._cache:
                return []
            
            # 全要件との類似度を計算
            similarities = []
            for req_id, req in self._cache.items():
                similarity = self._cosine_similarity(
                    embedding["vector"], 
                    req["embedding"]["vector"]
                )
                similarities.append((req, similarity))
            
            # 類似度でソートして上位を返す
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [req for req, _ in similarities[:limit]]
            
        except Exception as e:
            return {"error": str(e), "code": "SEARCH_ERROR", "details": None}
    
    def get_all(self) -> List[RequirementDict]:
        """全ての決定事項を取得"""
        return list(self._cache.values())
    
    def get_stats(self) -> Dict[str, any]:
        """統計情報を取得"""
        if not self._cache:
            return {
                "total": 0,
                "oldest": None,
                "newest": None,
                "file_path": str(self.file_path)
            }
        
        sorted_by_date = sorted(
            self._cache.values(), 
            key=lambda x: x['created_at']
        )
        
        return {
            "total": len(self._cache),
            "oldest": sorted_by_date[0]['created_at'].isoformat(),
            "newest": sorted_by_date[-1]['created_at'].isoformat(),
            "file_path": str(self.file_path)
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度を計算"""
        import math
        
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        norm1 = math.sqrt(sum(v * v for v in vec1))
        norm2 = math.sqrt(sum(v * v for v in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


def create_file_repository(file_path: str = None):
    """ファイルベースリポジトリを作成"""
    return FileBasedRepository(file_path)


# ===== テストコード =====

def test_file_repository_save_and_load():
    """ファイルリポジトリ_保存と読み込み_永続化"""
    import tempfile
    from ..domain.types import create_requirement, create_embedding
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        # 1つ目のリポジトリで保存
        repo1 = create_file_repository(temp_path)
        req = create_requirement("テスト決定事項", create_embedding([1.0, 0.0, 0.0]))
        result = repo1.save(req)
        assert isinstance(result, str)
        
        # 2つ目のリポジトリで読み込み
        repo2 = create_file_repository(temp_path)
        found = repo2.find_by_id(req["id"])
        assert "error" not in found
        assert found["text"] == "テスト決定事項"
        
    finally:
        os.unlink(temp_path)


def test_file_repository_append_mode():
    """ファイルリポジトリ_追記モード_累積保存"""
    import tempfile
    from ..domain.types import create_requirement, create_embedding
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        # 複数回の起動をシミュレート
        for i in range(3):
            repo = create_file_repository(temp_path)
            req = create_requirement(f"決定事項{i}", create_embedding([float(i), 0.0, 0.0]))
            repo.save(req)
        
        # 最終確認
        final_repo = create_file_repository(temp_path)
        all_reqs = final_repo.get_all()
        assert len(all_reqs) == 3
        assert {req["text"] for req in all_reqs} == {"決定事項0", "決定事項1", "決定事項2"}
        
    finally:
        os.unlink(temp_path)