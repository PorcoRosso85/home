#!/usr/bin/env python3
"""
テスト用JSONLデータ生成スクリプト
CLIツールのテレメトリーデータを模擬して生成
"""

import json
import random
import time
import sys
from datetime import datetime
from pathlib import Path
import argparse


class TelemetryGenerator:
    """テレメトリーデータ生成器"""
    
    def __init__(self):
        self.components = ['auth', 'api', 'database', 'cache', 'worker', 'scheduler']
        self.operations = ['query', 'update', 'delete', 'connect', 'process', 'validate']
        self.endpoints = ['/api/users', '/api/products', '/api/orders', '/api/stats', '/api/health']
        self.error_messages = [
            'Connection timeout',
            'Invalid credentials',
            'Resource not found',
            'Rate limit exceeded',
            'Database connection failed',
            'Memory allocation error'
        ]
    
    def generate_normal_event(self) -> dict:
        """正常なイベントを生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'info',
            'component': random.choice(self.components),
            'operation': random.choice(self.operations),
            'duration_ms': random.randint(10, 500),
            'memory_usage_mb': random.randint(100, 800),
            'process_name': f"cli-tool-{random.randint(1000, 9999)}"
        }
    
    def generate_api_event(self) -> dict:
        """APIイベントを生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'info',
            'component': 'api',
            'endpoint': random.choice(self.endpoints),
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'response_time_ms': random.randint(50, 2000),
            'status_code': random.choice([200, 200, 200, 201, 404, 500]),
            'user_id': f"user_{random.randint(1, 1000)}"
        }
    
    def generate_error_event(self) -> dict:
        """エラーイベントを生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'error',
            'severity': 'error',
            'component': random.choice(self.components),
            'message': random.choice(self.error_messages),
            'stack_trace': f"Error at line {random.randint(10, 1000)} in module.py",
            'error_code': f"ERR_{random.randint(1000, 9999)}"
        }
    
    def generate_warning_event(self) -> dict:
        """警告イベントを生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'warning',
            'component': random.choice(self.components),
            'message': 'High memory usage detected',
            'memory_usage_mb': random.randint(1024, 2048),
            'threshold_mb': 1024
        }
    
    def generate_slow_query_event(self) -> dict:
        """遅いクエリイベントを生成"""
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'warning',
            'component': 'database',
            'operation': 'query',
            'duration_ms': random.randint(5000, 15000),
            'query': f"SELECT * FROM large_table WHERE id = {random.randint(1, 1000000)}",
            'rows_examined': random.randint(100000, 1000000)
        }
    
    def generate_random_event(self) -> dict:
        """ランダムなイベントを生成"""
        event_types = [
            (self.generate_normal_event, 60),  # 60% の確率
            (self.generate_api_event, 20),     # 20% の確率
            (self.generate_error_event, 10),   # 10% の確率
            (self.generate_warning_event, 5),  # 5% の確率
            (self.generate_slow_query_event, 5) # 5% の確率
        ]
        
        # 重み付きランダム選択
        total = sum(weight for _, weight in event_types)
        r = random.randint(1, total)
        
        current = 0
        for generator, weight in event_types:
            current += weight
            if r <= current:
                return generator()
        
        return self.generate_normal_event()


def main():
    parser = argparse.ArgumentParser(description='Generate test JSONL telemetry data')
    parser.add_argument('output', help='Output JSONL file path')
    parser.add_argument('--rate', type=float, default=1.0, 
                       help='Events per second (default: 1.0)')
    parser.add_argument('--burst', action='store_true',
                       help='Generate burst of events periodically')
    parser.add_argument('--count', type=int, default=0,
                       help='Total number of events to generate (0 = infinite)')
    
    args = parser.parse_args()
    
    generator = TelemetryGenerator()
    output_path = Path(args.output)
    
    # ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating telemetry data to: {output_path}")
    print(f"Rate: {args.rate} events/second")
    print("Press Ctrl+C to stop")
    
    event_count = 0
    burst_counter = 0
    
    try:
        with open(output_path, 'a', encoding='utf-8') as f:
            while args.count == 0 or event_count < args.count:
                # バーストモード：30秒ごとに10秒間高頻度で生成
                if args.burst:
                    burst_counter += 1
                    if burst_counter % 30 < 10:
                        events_this_second = int(args.rate * 5)  # 5倍速
                    else:
                        events_this_second = int(args.rate)
                else:
                    events_this_second = int(args.rate) if args.rate >= 1 else 1
                
                # 1秒あたりのイベント生成
                for _ in range(events_this_second):
                    event = generator.generate_random_event()
                    f.write(json.dumps(event) + '\n')
                    f.flush()  # 即座に書き込み
                    event_count += 1
                    
                    if args.count > 0 and event_count >= args.count:
                        break
                
                # レート制御
                if args.rate < 1:
                    time.sleep(1.0 / args.rate)
                else:
                    time.sleep(1.0)
                    
    except KeyboardInterrupt:
        print(f"\nGenerated {event_count} events")


if __name__ == "__main__":
    main()