"""
Tests for Version Service
"""
from datetime import datetime
from .version_service import create_version_service


def test_version_service_track_change_creates_version():
    """version_service_track_change_バージョン作成_成功を返す"""
    # モックリポジトリ
    executions = []
    requirements = {
        "req_001": {
            "id": "req_001",
            "title": "Test Requirement",
            "description": "Test description",
            "status": "proposed",
            "embedding": [0.1] * 50,
            "created_at": datetime.now()
        }
    }
    
    def mock_execute(query, params=None):
        executions.append((query, params))
        return MockResult([])
    
    def mock_find(req_id):
        return requirements.get(req_id, {"type": "NotFoundError"})
    
    repository = {
        "execute": mock_execute,
        "find_requirement": mock_find,
        "save_requirement": lambda r: r
    }
    
    service = create_version_service(repository)
    
    # 変更を追跡
    result = service["track_requirement_change"]("req_001", "UPDATE", "test_user", "Updated description")
    
    assert "version_id" in result
    assert "snapshot_id" in result
    assert "location_uri" in result
    assert result["status"] == "tracked"
    assert len(executions) > 5  # 複数のクエリが実行される


def test_version_service_history_returns_sorted_versions():
    """version_service_history_履歴取得_時系列順で返す"""
    # モックデータ
    history_data = [
        ({
            "snapshot_id": "req_001@v1",
            "title": "Version 1"
        }, {
            "id": "v1",
            "timestamp": "2024-01-01T00:00:00",
            "author": "user1",
            "change_reason": "Initial"
        }),
        ({
            "snapshot_id": "req_001@v2",
            "title": "Version 2"
        }, {
            "id": "v2",
            "timestamp": "2024-01-02T00:00:00",
            "author": "user2",
            "change_reason": "Update"
        })
    ]
    
    def mock_execute(query, params=None):
        if "ORDER BY v.timestamp DESC" in query:
            return create_mock_result(history_data)
        return create_mock_result([])
    
    repository = {
        "execute": mock_execute,
        "find_requirement": lambda id: {},
        "save_requirement": lambda r: r
    }
    
    service = create_version_service(repository)
    
    # 履歴を取得
    history = service["get_requirement_history"]("req_001")
    
    assert len(history) == 2
    assert history[0]["version_id"] == "v1"
    assert history[1]["version_id"] == "v2"


# テスト用ヘルパー関数
def create_mock_result(data):
    """テスト用のモック結果オブジェクトを作成"""
    items = data if isinstance(data, list) else [data]
    index = [0]  # クロージャで状態を保持
    
    def has_next():
        return index[0] < len(items)
    
    def get_next():
        if has_next():
            result = items[index[0]]
            index[0] += 1
            return result
        return None
    
    # オブジェクト風のアクセスを提供
    mock = type('MockResult', (), {
        'has_next': has_next,
        'get_next': get_next,
        '_data': items
    })()
    
    return mock


class MockResult:
    """Mock result class for testing"""
    def __init__(self, data):
        self._data = data if isinstance(data, list) else [data]
        self._index = 0
    
    def has_next(self):
        return self._index < len(self._data)
    
    def get_next(self):
        if self.has_next():
            result = self._data[self._index]
            self._index += 1
            return result
        return None