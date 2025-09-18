#!/usr/bin/env python3
"""JSONL Monitor - 最小構成TDD実装"""
import json
import time
import os
import tempfile
from typing import Dict, Any, Callable, List, Optional


class JSONLMonitor:
    """JSONLファイル監視の最小実装"""
    
    def __init__(self):
        self.rules: List[Dict[str, Callable]] = []
        self.file_positions: Dict[str, int] = {}
        self.on_error: Optional[Callable] = None
    
    def add_rule(self, condition: Callable[[Dict], bool], action: Callable[[Dict], None]):
        """アラートルールを追加"""
        self.rules.append({'condition': condition, 'action': action})
    
    def process_data(self, data: Dict[str, Any]):
        """データに対してルールを適用"""
        for rule in self.rules:
            if rule['condition'](data):
                rule['action'](data)
    
    def tail_file(self, filepath: str, skip_existing: bool = False):
        """ファイルから新しい行を読み込んで処理"""
        if not os.path.exists(filepath):
            return
        
        if skip_existing and filepath not in self.file_positions:
            with open(filepath, 'rb') as f:
                f.seek(0, 2)
                self.file_positions[filepath] = f.tell()
            return
        
        last_position = self.file_positions.get(filepath, 0)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            f.seek(last_position)
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    self.process_data(data)
                except json.JSONDecodeError as e:
                    if self.on_error:
                        self.on_error(line, e)
            
            self.file_positions[filepath] = f.tell()


# ==============================================================================
# テスト = 仕様
# ==============================================================================

def test_jsonl_monitor_add_rule_単一ルール追加_成功():
    """アラートルールを1つ追加できることを確認"""
    monitor = JSONLMonitor()
    monitor.add_rule(lambda d: d.get("level") == "error", lambda d: None)
    assert len(monitor.rules) == 1


def test_jsonl_monitor_process_data_条件一致_アクション実行():
    """条件に一致した場合、アクションが実行されることを確認"""
    monitor = JSONLMonitor()
    called = []
    monitor.add_rule(lambda d: d.get("level") == "error", lambda d: called.append(d))
    
    monitor.process_data({"level": "error", "message": "test error"})
    assert len(called) == 1
    assert called[0]["message"] == "test error"
    
    monitor.process_data({"level": "info", "message": "test info"})
    assert len(called) == 1


def test_jsonl_monitor_process_data_複数ルール_該当のみ実行():
    """複数ルールがある場合、該当するルールのみ実行されることを確認"""
    monitor = JSONLMonitor()
    error_called = []
    warning_called = []
    
    monitor.add_rule(lambda d: d.get("level") == "error", lambda d: error_called.append(d))
    monitor.add_rule(lambda d: d.get("level") == "warning", lambda d: warning_called.append(d))
    
    monitor.process_data({"level": "error", "msg": "e1"})
    assert len(error_called) == 1 and len(warning_called) == 0
    
    monitor.process_data({"level": "warning", "msg": "w1"})
    assert len(error_called) == 1 and len(warning_called) == 1


def test_jsonl_monitor_tail_file_新規行読み込み_正常():
    """ファイルに追記された新しい行のみ読み込まれることを確認"""
    monitor = JSONLMonitor()
    processed = []
    monitor.add_rule(lambda d: True, lambda d: processed.append(d))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"id": 1, "message": "initial"}\n')
        temp_path = f.name
    
    try:
        monitor.tail_file(temp_path, skip_existing=True)
        assert len(processed) == 0
        
        with open(temp_path, 'a') as f:
            f.write('{"id": 2, "message": "added"}\n')
        
        monitor.tail_file(temp_path)
        assert len(processed) == 1 and processed[0]["id"] == 2
    finally:
        os.unlink(temp_path)


def test_jsonl_monitor_tail_file_無効JSON_スキップ():
    """無効なJSON行はスキップされ、有効な行は処理されることを確認"""
    monitor = JSONLMonitor()
    processed = []
    errors = []
    
    monitor.add_rule(lambda d: True, lambda d: processed.append(d))
    monitor.on_error = lambda line, error: errors.append((line, str(error)))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"valid": true}\ninvalid json\n{"also": "valid"}\n')
        temp_path = f.name
    
    try:
        monitor.tail_file(temp_path, skip_existing=False)
        assert len(processed) == 2
        assert processed[0]["valid"] is True
        assert processed[1]["also"] == "valid"
        assert len(errors) == 1 and errors[0][0] == "invalid json"
    finally:
        os.unlink(temp_path)


def test_jsonl_monitor_tail_file_位置記憶_重複なし():
    """ファイルの読み込み位置を記憶し、重複読み込みがないことを確認"""
    monitor = JSONLMonitor()
    processed = []
    monitor.add_rule(lambda d: True, lambda d: processed.append(d))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"id": 1}\n')
        temp_path = f.name
    
    try:
        monitor.tail_file(temp_path, skip_existing=False)
        assert len(processed) == 1
        
        monitor.tail_file(temp_path)
        assert len(processed) == 1
        
        with open(temp_path, 'a') as f:
            f.write('{"id": 2}\n')
        
        monitor.tail_file(temp_path)
        assert len(processed) == 2 and processed[1]["id"] == 2
    finally:
        os.unlink(temp_path)


# ==============================================================================
# 実行
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1 or "--test" in sys.argv:
        # テスト実行
        tests = [f for name, f in globals().items() if name.startswith("test_")]
        
        try:
            import pytest
            pytest.main([__file__, "-v"])
        except ImportError:
            for test in tests:
                try:
                    test()
                    print(f"✓ {test.__name__}")
                except AssertionError as e:
                    print(f"✗ {test.__name__}: {e}")
                    raise
            print(f"\nAll {len(tests)} tests passed! ✅")
    else:
        # 通常使用
        monitor = JSONLMonitor()
        
        # アラートルール設定
        monitor.add_rule(
            lambda d: d.get("level") == "error",
            lambda d: print(f"🚨 ERROR: {d.get('message', 'No message')}")
        )
        monitor.add_rule(
            lambda d: d.get("response_time_ms", 0) > 1000,
            lambda d: print(f"🐌 SLOW: {d.get('response_time_ms')}ms")
        )
        
        # ファイル監視
        filepath = sys.argv[1]
        print(f"Monitoring {filepath}... (Ctrl+C to stop)")
        
        try:
            monitor.tail_file(filepath, skip_existing=True)
            while True:
                monitor.tail_file(filepath)
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopped.")