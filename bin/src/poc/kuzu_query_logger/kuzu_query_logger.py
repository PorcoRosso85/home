"""
KuzuDB Query Logger
ACIDトランザクションが確定したクエリのみをログ化し、複数ノード間の同期を実現
"""

from typing import List, Dict, Union, Optional, TypedDict
from datetime import datetime
import hashlib
import json


# ========== 型定義 ==========

class LogEntry(TypedDict):
    """ログエントリーの型定義"""
    sequence_number: int
    timestamp: str
    query: str
    status: str  # "committed" | "rolled_back"
    checksum: str


class TransactionResult(TypedDict):
    """トランザクション結果の型定義"""
    success: bool
    queries_count: int
    error: Optional[str]


class ReplayResult(TypedDict):
    """ログ再生結果の型定義"""
    applied_count: int
    conflicts_count: int
    error: Optional[str]


class ErrorDict(TypedDict):
    """エラー情報の型定義"""
    error: str
    details: Optional[str]


# ========== REDフェーズテスト: トランザクション管理 ==========

def test_log_only_committed_transactions_成功時のみログ():
    """コミットされたトランザクションのみログ化される"""
    logger = KuzuQueryLogger("test.db")
    
    tx = logger.begin_transaction()
    tx.execute("CREATE (u:User {id: 1})")
    tx.execute("CREATE (u:User {id: 2})")
    tx.commit()
    
    logs = logger.get_logs()
    assert len(logs) == 2
    assert logs[0]["status"] == "committed"


def test_exclude_rolled_back_transactions_ロールバック除外():
    """ロールバックされたトランザクションはログ化されない"""
    logger = KuzuQueryLogger("test.db")
    
    tx = logger.begin_transaction()
    tx.execute("CREATE (u:User {id: 1})")
    tx.rollback()
    
    logs = logger.get_logs()
    assert len(logs) == 0


def test_atomic_transaction_logging_原子性保証():
    """トランザクション内の操作は全てまとめてログ化"""
    logger = KuzuQueryLogger("test.db")
    
    tx = logger.begin_transaction()
    tx.execute("CREATE (u:User {id: 1})")
    tx.execute("CREATE (p:Product {id: 1})")
    tx.execute("CREATE (u)-[:BOUGHT]->(p)")
    tx.commit()
    
    logs = logger.get_logs()
    assert len(logs) == 1  # 1つのトランザクションとして
    assert logs[0]["queries_count"] == 3


# ========== REDフェーズテスト: ログの整合性保証 ==========

def test_log_entry_immutability_ログ不変性():
    """一度記録されたログは変更不可"""
    logger = KuzuQueryLogger("test.db")
    
    logger.execute("CREATE (u:User {id: 1})")
    log_entry = logger.get_logs()[0]
    
    # ログエントリーの改竄を試みる
    try:
        log_entry["query"] = "CREATE (u:User {id: 2})"
        assert False, "ログエントリーが変更可能になっている"
    except ImmutabilityError:
        assert True


def test_log_entry_checksum_チェックサム検証():
    """各ログエントリーのチェックサムが正しく計算される"""
    logger = KuzuQueryLogger("test.db")
    
    logger.execute("CREATE (u:User {id: 1})")
    log_entry = logger.get_logs()[0]
    
    assert "checksum" in log_entry
    assert log_entry["checksum"] == calculate_checksum(log_entry)
    assert logger.verify_log_integrity() == True


def test_sequential_log_numbering_連番保証():
    """ログエントリーは厳密な連番を持つ"""
    logger = KuzuQueryLogger("test.db")
    
    logger.execute("CREATE (u:User {id: 1})")
    logger.execute("CREATE (u:User {id: 2})")
    
    logs = logger.get_logs()
    assert logs[0]["sequence_number"] == 1
    assert logs[1]["sequence_number"] == 2


# ========== REDフェーズテスト: 複数ノード同期 ==========

def test_replay_logs_on_replica_レプリカでの再生():
    """プライマリのログをレプリカで再生できる"""
    primary = KuzuQueryLogger("primary.db")
    replica = KuzuQueryLogger("replica.db")
    
    primary.execute("CREATE (u:User {id: 1, name: 'Alice'})")
    primary.execute("CREATE (p:Product {id: 1, name: 'Book'})")
    
    result = replica.replay_from(primary)
    
    assert result["applied_count"] == 2
    assert result["conflicts_count"] == 0
    
    # レプリカでデータが同期されている
    query_result = replica.query("MATCH (u:User {id: 1}) RETURN u.name")
    assert query_result[0] == "Alice"


def test_idempotent_replay_冪等性保証():
    """同じログを複数回再生しても結果は同じ"""
    primary = KuzuQueryLogger("primary.db")
    replica = KuzuQueryLogger("replica.db")
    
    primary.execute("CREATE (u:User {id: 1})")
    
    # 2回再生
    replica.replay_from(primary)
    replica.replay_from(primary)
    
    # ユーザーは1人だけ
    count_result = replica.query("MATCH (u:User) RETURN count(u) as count")
    assert count_result[0]["count"] == 1


def test_partial_sync_差分同期():
    """特定時点以降の差分のみ同期"""
    primary = KuzuQueryLogger("primary.db")
    replica = KuzuQueryLogger("replica.db")
    
    primary.execute("CREATE (u:User {id: 1})")
    checkpoint = primary.get_last_log_timestamp()
    
    primary.execute("CREATE (u:User {id: 2})")
    primary.execute("CREATE (u:User {id: 3})")
    
    result = replica.replay_from(primary, since=checkpoint)
    
    assert result["applied_count"] == 2
    # レプリカには2と3のみ存在
    count_result = replica.query("MATCH (u:User) RETURN count(u) as count")
    assert count_result[0]["count"] == 2


# ========== REDフェーズテスト: エラー処理と回復 ==========

def test_handle_replay_conflicts_競合処理():
    """再生時の競合を適切に処理"""
    primary = KuzuQueryLogger("primary.db")
    replica = KuzuQueryLogger("replica.db")
    
    # レプリカに独自のデータ
    replica.execute("CREATE (u:User {id: 1, name: 'Bob'})")
    
    # プライマリから同じIDのユーザー
    primary.execute("CREATE (u:User {id: 1, name: 'Alice'})")
    
    result = replica.replay_from(primary, conflict_strategy="skip")
    assert result["conflicts_count"] == 1
    assert result["applied_count"] == 0


def test_crash_recovery_クラッシュリカバリ():
    """クラッシュ後もログの整合性を保つ"""
    logger = KuzuQueryLogger("test.db")
    
    # 正常なログエントリー
    logger.execute("CREATE (u:User {id: 1})")
    
    # 不完全なログエントリーをシミュレート
    logger._write_partial_log("CREATE (u:User")
    
    # 再起動後の回復
    logger2 = KuzuQueryLogger("test.db")
    assert logger2.verify_log_integrity() == True
    
    logs = logger2.get_logs()
    # 不完全なログは除外される
    assert len(logs) == 1
    assert logs[0]["status"] == "committed"


# ========== 実行用コード ==========

if __name__ == "__main__":
    print("=== KuzuDB Query Logger - TDD RED PHASE ===\n")
    
    tests = [
        # トランザクション管理
        test_log_only_committed_transactions_成功時のみログ,
        test_exclude_rolled_back_transactions_ロールバック除外,
        test_atomic_transaction_logging_原子性保証,
        # ログの整合性保証
        test_log_entry_immutability_ログ不変性,
        test_log_entry_checksum_チェックサム検証,
        test_sequential_log_numbering_連番保証,
        # 複数ノード同期
        test_replay_logs_on_replica_レプリカでの再生,
        test_idempotent_replay_冪等性保証,
        test_partial_sync_差分同期,
        # エラー処理と回復
        test_handle_replay_conflicts_競合処理,
        test_crash_recovery_クラッシュリカバリ,
    ]
    
    failed = 0
    for test in tests:
        print(f"実行中: {test.__name__}")
        try:
            test()
            print("  ✗ テストが成功しました（実装が既に存在？）")
        except NameError as e:
            print(f"  ✓ RED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✓ RED: {type(e).__name__}: {e}")
            failed += 1
        print()
    
    print(f"=== 結果: {failed}/{len(tests)} テストが期待通り失敗 ===")