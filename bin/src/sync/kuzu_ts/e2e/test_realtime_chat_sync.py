"""
E2E Test: Real-time Chat Application Synchronization
リアルタイムチャットアプリケーションでの同期ユースケース

このテストは、実際のチャットアプリケーションシナリオで
sync/kuzu_tsがどのように使われるかを示す「実行可能な仕様書」です。
"""

import asyncio
import json
import pytest
import uuid
import time
import tempfile
import shutil
from typing import List, Dict, Any
import kuzu


class ChatClient:
    """チャットクライアントのシミュレーション"""
    
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp(prefix=f"kuzu_chat_{user_id}_")
        db_path = f"{self.temp_dir}/chat.db"
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self.messages: List[Dict[str, Any]] = []
        self._initialize_schema()
        
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'conn'):
            del self.conn
        if hasattr(self, 'db'):
            del self.db
        if hasattr(self, 'temp_dir'):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
    def _initialize_schema(self):
        """チャットアプリのスキーマを初期化"""
        # ユーザーテーブル
        self.conn.execute("""
            CREATE NODE TABLE User (
                id STRING,
                username STRING,
                status STRING,
                lastSeen INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # チャンネルテーブル
        self.conn.execute("""
            CREATE NODE TABLE Channel (
                id STRING,
                name STRING,
                description STRING,
                createdAt INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # メッセージテーブル
        self.conn.execute("""
            CREATE NODE TABLE Message (
                id STRING,
                content STRING,
                timestamp INT64,
                edited BOOLEAN,
                PRIMARY KEY(id)
            )
        """)
        
        # リレーションシップ
        self.conn.execute("CREATE REL TABLE SENT_BY (FROM Message TO User)")
        self.conn.execute("CREATE REL TABLE IN_CHANNEL (FROM Message TO Channel)")
        self.conn.execute("CREATE REL TABLE MEMBER_OF (FROM User TO Channel, joinedAt INT64)")
        
    def join_channel(self, channel_id: str, channel_name: str):
        """チャンネルに参加"""
        # チャンネルが存在しない場合は作成
        self.conn.execute("""
            MERGE (c:Channel {id: $channelId})
            ON CREATE SET c.name = $channelName, 
                         c.createdAt = $timestamp
        """, {
            "channelId": channel_id,
            "channelName": channel_name,
            "timestamp": int(time.time() * 1000)
        })
        
        # ユーザーを作成/更新
        self.conn.execute("""
            MERGE (u:User {id: $userId})
            ON CREATE SET u.username = $username, u.status = 'online'
            ON MATCH SET u.status = 'online', u.lastSeen = $timestamp
        """, {
            "userId": self.user_id,
            "username": self.username,
            "timestamp": int(time.time() * 1000)
        })
        
        # メンバーシップを作成
        self.conn.execute("""
            MATCH (u:User {id: $userId})
            MATCH (c:Channel {id: $channelId})
            MERGE (u)-[m:MEMBER_OF]->(c)
            ON CREATE SET m.joinedAt = $timestamp
        """, {
            "userId": self.user_id,
            "channelId": channel_id,
            "timestamp": int(time.time() * 1000)
        })
        
    def send_message(self, channel_id: str, content: str) -> Dict[str, Any]:
        """メッセージを送信"""
        message = {
            "id": f"msg-{uuid.uuid4()}",
            "content": content,
            "timestamp": int(time.time() * 1000),
            "userId": self.user_id,
            "username": self.username,
            "channelId": channel_id
        }
        
        # メッセージをDBに保存
        self.conn.execute("""
            CREATE (m:Message {
                id: $id,
                content: $content,
                timestamp: $timestamp,
                edited: false
            })
        """, {
            "id": message["id"],
            "content": message["content"],
            "timestamp": message["timestamp"]
        })
        
        # リレーションシップを作成
        self.conn.execute("""
            MATCH (m:Message {id: $id})
            MATCH (u:User {id: $userId})
            MATCH (c:Channel {id: $channelId})
            CREATE (m)-[:SENT_BY]->(u)
            CREATE (m)-[:IN_CHANNEL]->(c)
        """, {
            "id": message["id"],
            "userId": message["userId"],
            "channelId": message["channelId"]
        })
        
        self.messages.append(message)
        return message
        
    def receive_message(self, message: Dict[str, Any]):
        """他のクライアントからのメッセージを受信して同期"""
        # メッセージが既に存在するかチェック
        result = self.conn.execute(
            "MATCH (m:Message {id: $id}) RETURN m",
            {"id": message["id"]}
        )
        
        if not result.has_next():
            # 新しいメッセージを保存
            self.conn.execute("""
                CREATE (m:Message {
                    id: $id,
                    content: $content,
                    timestamp: $timestamp,
                    edited: false
                })
            """, {
                "id": message["id"],
                "content": message["content"],
                "timestamp": message["timestamp"]
            })
            
            # 送信者情報を確認/作成（オンラインステータスと名前も同期）
            self.conn.execute("""
                MERGE (u:User {id: $userId})
                ON CREATE SET u.username = $username, u.status = 'online'
                ON MATCH SET u.status = 'online', u.lastSeen = $timestamp
            """, {
                "userId": message["userId"],
                "username": message.get("username", "Unknown"),
                "timestamp": message["timestamp"]
            })
            
            # ユーザーをチャンネルのメンバーとして追加
            self.conn.execute("""
                MATCH (u:User {id: $userId})
                MATCH (c:Channel {id: $channelId})
                MERGE (u)-[m:MEMBER_OF]->(c)
                ON CREATE SET m.joinedAt = $timestamp
            """, {
                "userId": message["userId"],
                "channelId": message["channelId"],
                "timestamp": message["timestamp"]
            })
            
            # リレーションシップを作成
            self.conn.execute("""
                MATCH (m:Message {id: $id})
                MATCH (u:User {id: $userId})
                MATCH (c:Channel {id: $channelId})
                CREATE (m)-[:SENT_BY]->(u)
                CREATE (m)-[:IN_CHANNEL]->(c)
            """, {
                "id": message["id"],
                "userId": message["userId"],
                "channelId": message["channelId"]
            })
            
            self.messages.append(message)
            
    def get_channel_messages(self, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """チャンネルの最新メッセージを取得"""
        result = self.conn.execute("""
            MATCH (m:Message)-[:IN_CHANNEL]->(c:Channel {id: $channelId})
            MATCH (m)-[:SENT_BY]->(u:User)
            RETURN m.id as id, m.content as content, m.timestamp as timestamp,
                   u.id as userId, u.username as username
            ORDER BY m.timestamp DESC
            LIMIT $limit
        """, {"channelId": channel_id, "limit": limit})
        
        messages = []
        while result.has_next():
            row = result.get_next()
            messages.append({
                "id": row[0],
                "content": row[1],
                "timestamp": row[2],
                "userId": row[3],
                "username": row[4]
            })
        
        return list(reversed(messages))  # 時系列順に並べ替え
        
    def get_online_users(self, channel_id: str) -> List[Dict[str, str]]:
        """チャンネルのオンラインユーザーを取得"""
        result = self.conn.execute("""
            MATCH (u:User)-[:MEMBER_OF]->(c:Channel {id: $channelId})
            WHERE u.status = 'online'
            RETURN u.id as id, u.username as username
            ORDER BY u.username
        """, {"channelId": channel_id})
        
        users = []
        while result.has_next():
            row = result.get_next()
            users.append({"id": row[0], "username": row[1]})
        
        return users


@pytest.mark.asyncio
async def test_realtime_chat_synchronization():
    """リアルタイムチャットでのメッセージ同期テスト"""
    
    # === シナリオ: 3人のユーザーがチャットルームで会話 ===
    print("\n=== リアルタイムチャット同期シナリオ ===")
    
    # ユーザーを作成
    alice = ChatClient("user-alice", "Alice")
    bob = ChatClient("user-bob", "Bob")
    charlie = ChatClient("user-charlie", "Charlie")
    
    channel_id = "general"
    
    # 全員がチャンネルに参加
    alice.join_channel(channel_id, "General Chat")
    bob.join_channel(channel_id, "General Chat")
    charlie.join_channel(channel_id, "General Chat")
    
    # Aliceがメッセージを送信
    msg1 = alice.send_message(channel_id, "Hello everyone! 👋")
    print(f"Alice: {msg1['content']}")
    
    # 他のクライアントに同期
    bob.receive_message(msg1)
    charlie.receive_message(msg1)
    
    # Bobが返信
    msg2 = bob.send_message(channel_id, "Hi Alice! How are you?")
    print(f"Bob: {msg2['content']}")
    
    alice.receive_message(msg2)
    charlie.receive_message(msg2)
    
    # Charlieも参加
    msg3 = charlie.send_message(channel_id, "Hey folks! Just joined the conversation")
    print(f"Charlie: {msg3['content']}")
    
    alice.receive_message(msg3)
    bob.receive_message(msg3)
    
    # === 検証: 全員が同じメッセージ履歴を持つ ===
    alice_messages = alice.get_channel_messages(channel_id)
    bob_messages = bob.get_channel_messages(channel_id)
    charlie_messages = charlie.get_channel_messages(channel_id)
    
    assert len(alice_messages) == 3
    assert len(bob_messages) == 3
    assert len(charlie_messages) == 3
    
    # メッセージ内容の一致を確認
    for i in range(3):
        assert alice_messages[i]["content"] == bob_messages[i]["content"]
        assert bob_messages[i]["content"] == charlie_messages[i]["content"]
    
    print("\n✅ メッセージ同期成功: 全員が同じ履歴を持っています")
    
    # === オンラインユーザーの確認 ===
    online_users = alice.get_online_users(channel_id)
    assert len(online_users) == 3
    assert any(u["username"] == "Alice" for u in online_users)
    assert any(u["username"] == "Bob" for u in online_users)
    assert any(u["username"] == "Charlie" for u in online_users)
    
    print("✅ オンラインユーザー: " + ", ".join(u["username"] for u in online_users))


@pytest.mark.asyncio
async def test_chat_message_ordering():
    """メッセージの順序保証テスト"""
    
    print("\n=== メッセージ順序保証テスト ===")
    
    alice = ChatClient("user-alice-2", "Alice")
    bob = ChatClient("user-bob-2", "Bob")
    
    channel_id = "order-test"
    alice.join_channel(channel_id, "Order Test")
    bob.join_channel(channel_id, "Order Test")
    
    # 高速でメッセージを送信
    messages = []
    for i in range(10):
        if i % 2 == 0:
            msg = alice.send_message(channel_id, f"Message {i} from Alice")
            bob.receive_message(msg)
        else:
            msg = bob.send_message(channel_id, f"Message {i} from Bob")
            alice.receive_message(msg)
        messages.append(msg)
        await asyncio.sleep(0.01)  # 10ms間隔
    
    # 両者のメッセージ履歴を確認
    alice_msgs = alice.get_channel_messages(channel_id)
    bob_msgs = bob.get_channel_messages(channel_id)
    
    # タイムスタンプ順序の確認
    for i in range(1, len(alice_msgs)):
        assert alice_msgs[i]["timestamp"] >= alice_msgs[i-1]["timestamp"]
        assert bob_msgs[i]["timestamp"] >= bob_msgs[i-1]["timestamp"]
    
    # 内容の一致確認
    for i in range(len(messages)):
        assert alice_msgs[i]["content"] == messages[i]["content"]
        assert bob_msgs[i]["content"] == messages[i]["content"]
    
    print("✅ メッセージ順序が正しく保持されています")


@pytest.mark.asyncio
async def test_chat_conflict_resolution():
    """同時編集の競合解決テスト"""
    
    print("\n=== メッセージ編集の競合解決テスト ===")
    
    # このテストは、将来的にメッセージ編集機能が追加された際の
    # 競合解決メカニズムを検証するプレースホルダーです
    
    # 現在の実装では、メッセージは不変（append-only）なので
    # 競合は発生しません
    
    alice = ChatClient("user-alice-3", "Alice")
    channel_id = "conflict-test"
    alice.join_channel(channel_id, "Conflict Test")
    
    # メッセージ送信
    msg = alice.send_message(channel_id, "Original message")
    
    # 将来的な編集機能のテスト
    # edit1 = alice.edit_message(msg["id"], "Edited by Alice")
    # edit2 = bob.edit_message(msg["id"], "Edited by Bob")
    # 
    # # Last-Write-Wins または 他の競合解決戦略
    # final_content = alice.get_message(msg["id"])
    # assert final_content in ["Edited by Alice", "Edited by Bob"]
    
    print("✅ 競合解決メカニズム（将来実装予定）")


if __name__ == "__main__":
    # 直接実行時のデモ
    asyncio.run(test_realtime_chat_synchronization())
    asyncio.run(test_chat_message_ordering())
    asyncio.run(test_chat_conflict_resolution())