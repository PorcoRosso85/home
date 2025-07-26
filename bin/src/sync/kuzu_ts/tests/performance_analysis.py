"""
Performance analysis for E2E test_concurrent_increments
"""

import asyncio
import time
import pytest
import json
import uuid
from typing import Dict, List, Tuple
from e2e_test import SyncClient, WebSocketServerFixture

class PerformanceMetrics:
    """Performance metrics collector"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "connect_time": [],
            "send_event_time": [],
            "receive_event_time": [],
            "asyncio_sleep_time": [],
            "ws_latency": [],
            "total_time": []
        }
        
    def record(self, metric: str, duration: float):
        if metric not in self.metrics:
            self.metrics[metric] = []
        self.metrics[metric].append(duration)
        
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        summary = {}
        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    "count": len(values),
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        return summary


async def measure_concurrent_increments():
    """Measure performance of concurrent increments test"""
    
    metrics = PerformanceMetrics()
    server = WebSocketServerFixture()
    
    try:
        # Start server
        server.start_server()
        await asyncio.sleep(2)  # Wait for server startup
        
        # Overall test timing
        test_start = time.perf_counter()
        
        clients = []
        
        # Measure connection time for each client
        for i in range(5):
            client = SyncClient(f"perf-client-{i}")
            
            connect_start = time.perf_counter()
            await client.connect()
            connect_time = time.perf_counter() - connect_start
            metrics.record("connect_time", connect_time)
            
            clients.append(client)
        
        # Measure initial query
        initial_query_start = time.perf_counter()
        initial_query = {
            "id": str(uuid.uuid4()),
            "template": "QUERY_COUNTER",
            "params": {"counterId": "shared-counter"},
            "clientId": clients[0].client_id,
            "timestamp": int(time.time() * 1000)
        }
        await clients[0].send_event(initial_query)
        
        # Measure asyncio.sleep overhead
        sleep_start = time.perf_counter()
        await asyncio.sleep(0.2)
        sleep_time = time.perf_counter() - sleep_start
        metrics.record("asyncio_sleep_time", sleep_time)
        
        initial_query_time = time.perf_counter() - initial_query_start
        metrics.record("send_event_time", initial_query_time)
        
        # Measure concurrent increment operations
        tasks = []
        send_times = []
        
        for i, client in enumerate(clients):
            event = {
                "id": str(uuid.uuid4()),
                "template": "INCREMENT_COUNTER",
                "params": {"counterId": "shared-counter", "amount": 1},
                "clientId": client.client_id,
                "timestamp": int(time.time() * 1000)
            }
            
            # Create coroutine with timing
            async def timed_send(c, e):
                start = time.perf_counter()
                await c.send_event(e)
                duration = time.perf_counter() - start
                return duration
            
            tasks.append(timed_send(client, event))
        
        # Execute all increments concurrently
        concurrent_start = time.perf_counter()
        send_durations = await asyncio.gather(*tasks)
        concurrent_time = time.perf_counter() - concurrent_start
        
        for duration in send_durations:
            metrics.record("send_event_time", duration)
        
        # Measure sleep after concurrent operations
        sleep_start = time.perf_counter()
        await asyncio.sleep(1)
        sleep_time = time.perf_counter() - sleep_start
        metrics.record("asyncio_sleep_time", sleep_time)
        
        # Measure event propagation time
        propagation_start = time.perf_counter()
        received_counts = []
        for client in clients:
            events = client.get_received_events()
            increment_events = [e for e in events if e["template"] == "INCREMENT_COUNTER"]
            received_counts.append(len(increment_events))
        propagation_time = time.perf_counter() - propagation_start
        metrics.record("receive_event_time", propagation_time)
        
        # Measure query verification
        query_tasks = []
        for client in clients:
            query_event = {
                "id": str(uuid.uuid4()),
                "template": "QUERY_COUNTER",
                "params": {"counterId": "shared-counter"},
                "clientId": client.client_id,
                "timestamp": int(time.time() * 1000)
            }
            
            async def timed_query(c, e):
                start = time.perf_counter()
                await c.send_event(e)
                duration = time.perf_counter() - start
                return duration
            
            query_tasks.append(timed_query(client, query_event))
        
        query_durations = await asyncio.gather(*query_tasks)
        for duration in query_durations:
            metrics.record("send_event_time", duration)
        
        # Final sleep measurement
        sleep_start = time.perf_counter()
        await asyncio.sleep(0.5)
        sleep_time = time.perf_counter() - sleep_start
        metrics.record("asyncio_sleep_time", sleep_time)
        
        # Total test time
        total_time = time.perf_counter() - test_start
        metrics.record("total_time", total_time)
        
        # Cleanup
        for client in clients:
            await client.disconnect()
        
    finally:
        server.stop_server()
    
    return metrics


async def main():
    """Run performance analysis"""
    
    print("Running performance analysis for test_concurrent_increments...")
    print("=" * 60)
    
    # Run multiple iterations to get average metrics
    iterations = 3
    all_metrics = []
    
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}")
        metrics = await measure_concurrent_increments()
        all_metrics.append(metrics)
        
        # Brief pause between iterations
        await asyncio.sleep(2)
    
    # Aggregate results
    print("\n" + "=" * 60)
    print("PERFORMANCE ANALYSIS RESULTS")
    print("=" * 60)
    
    # Combine all metrics
    combined = PerformanceMetrics()
    for m in all_metrics:
        for metric, values in m.metrics.items():
            for value in values:
                combined.record(metric, value)
    
    # Display summary
    summary = combined.get_summary()
    
    total_test_time = summary.get("total_time", {}).get("average", 0)
    total_sleep_time = summary.get("asyncio_sleep_time", {}).get("total", 0)
    
    print(f"\n1. EXECUTION TIME BREAKDOWN:")
    print(f"   - Total test time: {total_test_time:.3f}s")
    print(f"   - Connection time (avg): {summary.get('connect_time', {}).get('average', 0):.3f}s")
    print(f"   - Send event time (avg): {summary.get('send_event_time', {}).get('average', 0):.3f}s")
    print(f"   - Event receive time: {summary.get('receive_event_time', {}).get('average', 0):.3f}s")
    
    print(f"\n2. BOTTLENECK ANALYSIS:")
    print(f"   - Total asyncio.sleep time: {total_sleep_time:.3f}s ({total_sleep_time/total_test_time*100:.1f}% of total)")
    print(f"   - WebSocket operations: {summary.get('send_event_time', {}).get('total', 0):.3f}s")
    print(f"   - Connection overhead: {summary.get('connect_time', {}).get('total', 0):.3f}s")
    
    print(f"\n3. OPTIMIZATION OPPORTUNITIES:")
    
    # Calculate potential savings
    sleep_overhead = total_sleep_time / total_test_time * 100
    if sleep_overhead > 50:
        print(f"   ✗ asyncio.sleep accounts for {sleep_overhead:.1f}% of test time")
        print(f"     → Reduce sleep durations or use event-driven waiting")
    
    avg_send_time = summary.get('send_event_time', {}).get('average', 0)
    if avg_send_time > 0.01:  # 10ms threshold
        print(f"   ✗ WebSocket send latency is high: {avg_send_time*1000:.1f}ms")
        print(f"     → Consider batching events or optimizing serialization")
    
    connection_time = summary.get('connect_time', {}).get('average', 0)
    if connection_time > 0.1:  # 100ms threshold
        print(f"   ✗ Connection time is slow: {connection_time*1000:.1f}ms per client")
        print(f"     → Consider connection pooling or persistent connections")
    
    print(f"\n4. RECOMMENDATIONS:")
    print(f"   - Replace fixed sleeps with event-based synchronization")
    print(f"   - Implement WebSocket message acknowledgments")
    print(f"   - Use concurrent.futures for better task management")
    print(f"   - Add connection reuse between test cases")


if __name__ == "__main__":
    asyncio.run(main())