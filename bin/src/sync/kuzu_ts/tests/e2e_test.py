"""
E2E tests for KuzuDB WebSocket synchronization
unified_syncのWebSocketテストをPythonに移植
"""

import asyncio
import json
import pytest
import uuid
import websockets
from typing import List, Dict, Any
import subprocess
import time
import os
import signal

class SyncClient:
    """WebSocket同期クライアント"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.ws = None
        self.received_events: List[Dict[str, Any]] = []
        self.connected = False
        self.history_events: List[Dict[str, Any]] = []  # 履歴イベント用
        
    async def connect(self, url: str = "ws://localhost:8080"):
        """WebSocketサーバーに接続"""
        ws_url = f"{url}?clientId={self.client_id}"
        self.ws = await websockets.connect(ws_url)
        self.connected = True
        
        # 非同期でメッセージを受信
        asyncio.create_task(self._receive_messages())
        
        # 接続確認メッセージを待つ
        await asyncio.sleep(0.1)
        
    async def _receive_messages(self):
        """バックグラウンドでメッセージを受信"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data["type"] == "event":
                    self.received_events.append(data["payload"])
                elif data["type"] == "connected":
                    print(f"Client {self.client_id} connected")
                elif data["type"] == "history":
                    # 履歴メッセージを受信
                    self.history_events = data.get("events", [])
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            
    async def send_event(self, event: Dict[str, Any]):
        """イベントを送信"""
        if not self.ws or not self.connected:
            raise RuntimeError("Not connected")
            
        await self.ws.send(json.dumps({
            "type": "event",
            "payload": event
        }))
        
    async def disconnect(self):
        """切断"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            
    def get_received_events(self) -> List[Dict[str, Any]]:
        """受信したイベントを取得"""
        return self.received_events.copy()
    
    async def query_state(self, cypher: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        KuzuDBにクエリを送信してステートを照会
        
        Args:
            cypher: Cypherクエリ文字列
            params: クエリパラメータ（オプション）
            
        Returns:
            クエリ結果を含む辞書
            
        Raises:
            RuntimeError: 接続されていない場合
            Exception: クエリ実行エラー
        """
        if not self.ws or not self.connected:
            raise RuntimeError("Not connected")
        
        # 一意のリクエストIDを生成
        request_id = str(uuid.uuid4())
        
        # クエリメッセージを送信
        await self.ws.send(json.dumps({
            "type": "query",
            "requestId": request_id,
            "cypher": cypher,
            "params": params or {}
        }))
        
        # レスポンスを待機（タイムアウト付き）
        timeout = 5.0  # 5秒のタイムアウト
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # タイムアウトチェック
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Query timeout after {timeout} seconds")
            
            # 少し待機
            await asyncio.sleep(0.1)
            
            # TODO: WebSocketサーバーがqueryレスポンスを実装したら、
            # ここで適切なレスポンスを待機する処理を追加
            # 現在はHTTP経由でクエリを実行
            break
        
        # 暫定的にHTTP経由でクエリを実行
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:8080/query',
                json={"cypher": cypher, "params": params or {}},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Query failed with status {response.status}: {error_text}")
                
                result = await response.json()
                if not result.get("success"):
                    raise Exception(f"Query failed: {result.get('error', 'Unknown error')}")
                
                return result.get("data", {})


class WebSocketServerFixture:
    """WebSocketサーバーのテストヘルパー"""
    
    def __init__(self):
        self.server_process = None
        
    def start_server(self, port: int = 8080):
        """WebSocketサーバーを起動"""
        # サーバーファイルのパスを取得
        server_path = os.path.join(os.path.dirname(__file__), "..", "core", "websocket", "server.ts")
        
        # サーバーを起動
        import shutil
        deno_path = shutil.which("deno")
        if not deno_path:
            raise RuntimeError("Deno not found in PATH")
            
        self.server_process = subprocess.Popen(
            [deno_path, "run", "--allow-net", "--allow-read", server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # プロセスグループを作成
        )
        
        # サーバーの起動を待つ
        time.sleep(2)
        
    def stop_server(self):
        """WebSocketサーバーを停止"""
        if self.server_process:
            # プロセスグループ全体にSIGTERMを送信
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process.wait(timeout=5)
            self.server_process = None


@pytest.fixture(scope="module")
def websocket_server():
    """WebSocketサーバーのフィクスチャ"""
    server = WebSocketServerFixture()
    server.start_server()
    yield server
    server.stop_server()


@pytest.mark.asyncio
async def test_multi_client_sync(websocket_server):
    """複数クライアント間の同期テスト"""
    # 3つのクライアントを作成
    client1 = SyncClient("test-client-1")
    client2 = SyncClient("test-client-2")
    client3 = SyncClient("test-client-3")
    
    try:
        # 全クライアントを接続
        await client1.connect()
        await client2.connect()
        await client3.connect()
        
        # Client1からイベントを送信
        event1 = {
            "id": str(uuid.uuid4()),
            "template": "CREATE_USER",
            "params": {"id": "user1", "name": "Alice"},
            "clientId": client1.client_id,
            "timestamp": int(time.time() * 1000)
        }
        await client1.send_event(event1)
        
        # 同期を待つ
        await asyncio.sleep(0.5)
        
        # Client2とClient3がイベントを受信したことを確認
        client2_events = client2.get_received_events()
        client3_events = client3.get_received_events()
        
        assert len(client2_events) == 1
        assert len(client3_events) == 1
        assert client2_events[0]["id"] == event1["id"]
        assert client3_events[0]["id"] == event1["id"]
        
        # Client2からも送信
        event2 = {
            "id": str(uuid.uuid4()),
            "template": "CREATE_USER",
            "params": {"id": "user2", "name": "Bob"},
            "clientId": client2.client_id,
            "timestamp": int(time.time() * 1000)
        }
        await client2.send_event(event2)
        
        await asyncio.sleep(0.5)
        
        # Client1とClient3が新しいイベントを受信
        client1_events = client1.get_received_events()
        client3_events = client3.get_received_events()
        
        assert len(client1_events) == 1
        assert len(client3_events) == 2  # event1とevent2の両方
        assert client1_events[0]["id"] == event2["id"]
        
    finally:
        # クリーンアップ
        await client1.disconnect()
        await client2.disconnect()
        await client3.disconnect()


@pytest.mark.asyncio
async def test_concurrent_increments(websocket_server):
    """並行インクリメント操作のテスト"""
    clients = []
    
    try:
        # 5つのクライアントを作成
        for i in range(5):
            client = SyncClient(f"increment-client-{i}")
            await client.connect()
            clients.append(client)
        
        # 初期状態を確認（カウンターが存在しない場合は0）
        initial_query = {
            "id": str(uuid.uuid4()),
            "template": "QUERY_COUNTER",
            "params": {"counterId": "shared-counter"},
            "clientId": clients[0].client_id,
            "timestamp": int(time.time() * 1000)
        }
        await clients[0].send_event(initial_query)
        await asyncio.sleep(0.2)
        
        initial_events = clients[0].get_received_events()
        initial_value_events = [e for e in initial_events if e.get("template") == "COUNTER_VALUE"]
        if initial_value_events:
            initial_value = initial_value_events[0].get("params", {}).get("value", 0)
        else:
            initial_value = 0
        
        # 全クライアントが同時にインクリメント
        tasks = []
        for i, client in enumerate(clients):
            event = {
                "id": str(uuid.uuid4()),
                "template": "INCREMENT_COUNTER",
                "params": {"counterId": "shared-counter", "amount": 1},
                "clientId": client.client_id,
                "timestamp": int(time.time() * 1000)
            }
            tasks.append(client.send_event(event))
        
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)
        
        # 各クライアントが他の4つのインクリメントを受信
        for client in clients:
            events = client.get_received_events()
            increment_events = [e for e in events if e["template"] == "INCREMENT_COUNTER"]
            assert len(increment_events) == 4  # 自分以外の4つ
        
        # クエリ検証: 各クライアントがカウンター値を確認
        query_tasks = []
        for client in clients:
            query_event = {
                "id": str(uuid.uuid4()),
                "template": "QUERY_COUNTER",
                "params": {"counterId": "shared-counter"},
                "clientId": client.client_id,
                "timestamp": int(time.time() * 1000)
            }
            query_tasks.append(client.send_event(query_event))
        
        await asyncio.gather(*query_tasks)
        await asyncio.sleep(0.5)
        
        # 各クライアントがクエリ結果を受信し、値が初期値+5であることを確認
        expected_value = initial_value + 5
        for i, client in enumerate(clients):
            events = client.get_received_events()
            query_responses = [e for e in events if e.get("template") == "COUNTER_VALUE"]
            
            # 最低1つのクエリレスポンスを受信
            assert len(query_responses) >= 1, f"Client {i} did not receive counter value"
            
            # 最新のカウンター値が期待値であることを確認
            latest_value = query_responses[-1].get("params", {}).get("value")
            assert latest_value == expected_value, f"Client {i} sees counter value {latest_value}, expected {expected_value}"
        
        # 異なるカウンターIDでも動作することを確認
        other_counter_event = {
            "id": str(uuid.uuid4()),
            "template": "INCREMENT_COUNTER",
            "params": {"counterId": "other-counter", "amount": 10},
            "clientId": clients[0].client_id,
            "timestamp": int(time.time() * 1000)
        }
        await clients[0].send_event(other_counter_event)
        
        # 他のカウンターの値を確認
        other_query = {
            "id": str(uuid.uuid4()),
            "template": "QUERY_COUNTER",
            "params": {"counterId": "other-counter"},
            "clientId": clients[0].client_id,
            "timestamp": int(time.time() * 1000)
        }
        await clients[0].send_event(other_query)
        await asyncio.sleep(0.2)
        
        final_events = clients[0].get_received_events()
        other_counter_values = [e for e in final_events if e.get("template") == "COUNTER_VALUE" 
                                and e.get("params", {}).get("counterId") == "other-counter"]
        assert len(other_counter_values) > 0, "Did not receive other counter value"
        assert other_counter_values[-1].get("params", {}).get("value") == 10, "Other counter should be 10"
            
    finally:
        # クリーンアップ
        for client in clients:
            await client.disconnect()


@pytest.mark.asyncio
async def test_history_sync(websocket_server):
    """履歴同期のテスト"""
    # 最初のクライアントがイベントを作成
    client1 = SyncClient("history-client-1")
    
    try:
        await client1.connect()
        
        # 複数のイベントを送信
        for i in range(3):
            event = {
                "id": str(uuid.uuid4()),
                "template": "CREATE_ITEM",
                "params": {"id": f"item-{i}", "name": f"Item {i}"},
                "clientId": client1.client_id,
                "timestamp": int(time.time() * 1000)
            }
            await client1.send_event(event)
            await asyncio.sleep(0.1)
        
        # Client1を切断
        await client1.disconnect()
        
        # 新しいクライアントが接続
        client2 = SyncClient("history-client-2")
        await client2.connect()
        
        # 履歴リクエストを送信
        await client2.ws.send(json.dumps({
            "type": "requestHistory",
            "fromPosition": 0
        }))
        
        # 履歴受信を待つ（タイムアウト付き）
        history_received = False
        
        # 最大5秒間、履歴イベントの受信を待つ
        for _ in range(50):  # 0.1秒 × 50回 = 5秒
            await asyncio.sleep(0.1)
            if len(client2.history_events) >= 3:
                history_received = True
                break
                
        assert history_received, "History was not received within timeout"
        assert len(client2.history_events) >= 3, f"Expected at least 3 history events, got {len(client2.history_events)}"
        
        await client2.disconnect()
        
    except Exception as e:
        if 'client1' in locals() and client1.connected:
            await client1.disconnect()
        if 'client2' in locals() and client2.connected:
            await client2.disconnect()
        raise


@pytest.mark.asyncio
async def test_broadcast_filtering(websocket_server):
    """ブロードキャストフィルタリングのテスト"""
    sender = SyncClient("sender-client")
    receiver1 = SyncClient("receiver-client-1")
    receiver2 = SyncClient("receiver-client-2")
    
    try:
        await sender.connect()
        await receiver1.connect()
        await receiver2.connect()
        
        # Receiver1は特定のテンプレートをサブスクライブ
        await receiver1.ws.send(json.dumps({
            "type": "subscribe",
            "template": "USER_EVENT"
        }))
        
        await asyncio.sleep(0.1)
        
        # USER_EVENTを送信
        user_event = {
            "id": str(uuid.uuid4()),
            "template": "USER_EVENT",
            "params": {"action": "login"},
            "clientId": sender.client_id,
            "timestamp": int(time.time() * 1000)
        }
        await sender.send_event(user_event)
        
        # 別のイベントも送信
        other_event = {
            "id": str(uuid.uuid4()),
            "template": "SYSTEM_EVENT",
            "params": {"action": "startup"},
            "clientId": sender.client_id,
            "timestamp": int(time.time() * 1000)
        }
        await sender.send_event(other_event)
        
        await asyncio.sleep(0.5)
        
        # Receiver1はUSER_EVENTのみ受信
        r1_events = receiver1.get_received_events()
        assert len(r1_events) == 1
        assert r1_events[0]["template"] == "USER_EVENT"
        
        # Receiver2は両方受信（サブスクリプションなし）
        r2_events = receiver2.get_received_events()
        assert len(r2_events) == 2
        
    finally:
        await sender.disconnect()
        await receiver1.disconnect()
        await receiver2.disconnect()


@pytest.mark.asyncio
async def test_query_state(websocket_server):
    """KuzuDBクエリ機能のテスト"""
    client = SyncClient("query-test-client")
    
    try:
        await client.connect()
        
        # イベントを送信してステートを作成
        user_event = {
            "id": str(uuid.uuid4()),
            "template": "CREATE_USER",
            "params": {"id": "test-user-123", "name": "Test User"},
            "clientId": client.client_id,
            "timestamp": int(time.time() * 1000)
        }
        await client.send_event(user_event)
        
        # イベントが処理されるまで待機
        await asyncio.sleep(0.5)
        
        # KuzuDBにクエリを送信
        # ユーザーを検索するクエリ
        result = await client.query_state(
            "MATCH (u:User {id: $userId}) RETURN u.name as name",
            {"userId": "test-user-123"}
        )
        
        # 結果を検証
        assert result is not None
        # 注: 実際の結果の構造は、ServerKuzuClientの実装に依存
        
        # 全ユーザーを取得するクエリ
        all_users = await client.query_state(
            "MATCH (u:User) RETURN u.id as id, u.name as name"
        )
        
        assert all_users is not None
        
    except Exception as e:
        # エラーの詳細を出力
        print(f"Query test failed: {e}")
        raise
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_query_state_error_handling(websocket_server):
    """クエリエラーハンドリングのテスト"""
    client = SyncClient("query-error-client")
    
    try:
        await client.connect()
        
        # 無効なクエリを送信
        with pytest.raises(Exception) as exc_info:
            await client.query_state("INVALID CYPHER QUERY")
        
        # エラーメッセージを確認
        assert "error" in str(exc_info.value).lower()
        
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_query_state_without_connection(websocket_server):
    """接続なしでのクエリテスト"""
    client = SyncClient("no-connection-client")
    
    # 接続せずにクエリを実行
    with pytest.raises(RuntimeError) as exc_info:
        await client.query_state("MATCH (n) RETURN n")
    
    assert "Not connected" in str(exc_info.value)


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v"])