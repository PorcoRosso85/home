"""Metrics and monitoring module.

This module handles all metrics-related operations including:
- Communication metrics tracking
- Performance measurement
- Cross-session connectivity verification
"""

import time
import subprocess
from typing import Dict, Any, List
from collections import defaultdict

from variables import SESSION_NAME


# Result pattern helpers
def _ok(data: Any) -> Dict[str, Any]:
    """Create success result."""
    return {"ok": True, "data": data, "error": None}


def _err(message: str, code: str = "error") -> Dict[str, Any]:
    """Create error result."""
    return {"ok": False, "data": None, "error": {"message": message, "code": code}}


# Global metrics storage (in-memory for simplicity)
_metrics_store = {
    "intra_session": {
        "count": 0,
        "total_latency": 0.0,
        "max_latency": 0.0,
        "min_latency": float('inf')
    },
    "cross_session": {
        "count": 0,
        "total_latency": 0.0,
        "max_latency": 0.0,
        "min_latency": float('inf')
    }
}


def get_communication_metrics() -> Dict[str, Any]:
    """Get communication metrics for monitoring.
    
    Returns:
        Dict with communication metrics
    """
    try:
        metrics = {
            "intra_session": {
                "count": _metrics_store["intra_session"]["count"],
                "avg_latency_ms": (
                    _metrics_store["intra_session"]["total_latency"] / _metrics_store["intra_session"]["count"]
                    if _metrics_store["intra_session"]["count"] > 0 else 0
                ),
                "max_latency_ms": _metrics_store["intra_session"]["max_latency"],
                "min_latency_ms": (
                    _metrics_store["intra_session"]["min_latency"]
                    if _metrics_store["intra_session"]["min_latency"] != float('inf') else 0
                )
            },
            "cross_session": {
                "count": _metrics_store["cross_session"]["count"],
                "avg_latency_ms": (
                    _metrics_store["cross_session"]["total_latency"] / _metrics_store["cross_session"]["count"]
                    if _metrics_store["cross_session"]["count"] > 0 else 0
                ),
                "max_latency_ms": _metrics_store["cross_session"]["max_latency"],
                "min_latency_ms": (
                    _metrics_store["cross_session"]["min_latency"]
                    if _metrics_store["cross_session"]["min_latency"] != float('inf') else 0
                )
            },
            "total_communications": (
                _metrics_store["intra_session"]["count"] +
                _metrics_store["cross_session"]["count"]
            )
        }
        
        return _ok(metrics)
        
    except Exception as e:
        return _err(f"Failed to get metrics: {str(e)}", "metrics_error")


def reset_metrics() -> Dict[str, Any]:
    """Reset all communication metrics.
    
    Returns:
        Dict with reset confirmation
    """
    try:
        global _metrics_store
        _metrics_store = {
            "intra_session": {
                "count": 0,
                "total_latency": 0.0,
                "max_latency": 0.0,
                "min_latency": float('inf')
            },
            "cross_session": {
                "count": 0,
                "total_latency": 0.0,
                "max_latency": 0.0,
                "min_latency": float('inf')
            }
        }
        
        return _ok({"reset": True, "timestamp": time.time()})
        
    except Exception as e:
        return _err(f"Failed to reset metrics: {str(e)}", "reset_error")


def _update_intra_session_metrics(latency_ms: float) -> None:
    """Update intra-session communication metrics.
    
    Args:
        latency_ms: Latency in milliseconds
    """
    _metrics_store["intra_session"]["count"] += 1
    _metrics_store["intra_session"]["total_latency"] += latency_ms
    _metrics_store["intra_session"]["max_latency"] = max(
        _metrics_store["intra_session"]["max_latency"], latency_ms
    )
    _metrics_store["intra_session"]["min_latency"] = min(
        _metrics_store["intra_session"]["min_latency"], latency_ms
    )


def _update_cross_session_metrics(latency_ms: float) -> None:
    """Update cross-session communication metrics.
    
    Args:
        latency_ms: Latency in milliseconds
    """
    _metrics_store["cross_session"]["count"] += 1
    _metrics_store["cross_session"]["total_latency"] += latency_ms
    _metrics_store["cross_session"]["max_latency"] = max(
        _metrics_store["cross_session"]["max_latency"], latency_ms
    )
    _metrics_store["cross_session"]["min_latency"] = min(
        _metrics_store["cross_session"]["min_latency"], latency_ms
    )


def verify_cross_session_connectivity(source_session: str, target_session: str) -> Dict[str, Any]:
    """Verify connectivity between two tmux sessions.
    
    Args:
        source_session: Source session name
        target_session: Target session name
        
    Returns:
        Dict with connectivity verification results
    """
    try:
        # Check if both sessions exist
        source_check = subprocess.run(
            ['tmux', 'has-session', '-t', source_session],
            capture_output=True,
            check=False
        )
        
        target_check = subprocess.run(
            ['tmux', 'has-session', '-t', target_session],
            capture_output=True,
            check=False
        )
        
        if source_check.returncode != 0:
            return _err(f"Source session does not exist: {source_session}", "source_missing")
        
        if target_check.returncode != 0:
            return _err(f"Target session does not exist: {target_session}", "target_missing")
        
        # Test sending a message (simulation)
        start_time = time.time()
        
        test_result = subprocess.run(
            ['tmux', 'send-keys', '-t', f"{target_session}:0", '', 'Enter'],
            capture_output=True,
            check=False
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if test_result.returncode == 0:
            _update_cross_session_metrics(latency_ms)
            
            return _ok({
                "source": source_session,
                "target": target_session,
                "connected": True,
                "latency_ms": latency_ms
            })
        else:
            return _err(f"Failed to send test message", "send_failed")
            
    except Exception as e:
        return _err(f"Failed to verify connectivity: {str(e)}", "connectivity_error")


def send_reliable_cross_session_message(target: str, message: str, retry_count: int = 3, timeout_ms: int = 1000) -> Dict[str, Any]:
    """Send a message reliably to another session with retries.
    
    Args:
        target: Target session or window
        message: Message to send
        retry_count: Number of retry attempts
        timeout_ms: Timeout per attempt in milliseconds
        
    Returns:
        Dict with send status
    """
    attempts = 0
    last_error = None
    
    while attempts < retry_count:
        attempts += 1
        start_time = time.time()
        
        try:
            # Try to send the message
            result = subprocess.run(
                ['tmux', 'send-keys', '-t', target, message, 'Enter'],
                capture_output=True,
                timeout=timeout_ms / 1000,
                check=False
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # Determine if this is cross-session or intra-session
                if ':' in target and not target.startswith(SESSION_NAME):
                    _update_cross_session_metrics(latency_ms)
                else:
                    _update_intra_session_metrics(latency_ms)
                
                return _ok({
                    "target": target,
                    "message": message,
                    "attempts": attempts,
                    "latency_ms": latency_ms
                })
            else:
                last_error = f"Send failed: {result.stderr.decode() if result.stderr else 'Unknown error'}"
                
        except subprocess.TimeoutExpired:
            last_error = f"Timeout after {timeout_ms}ms"
        except Exception as e:
            last_error = str(e)
        
        # Wait before retry
        if attempts < retry_count:
            time.sleep(0.1)
    
    return _err(f"Failed after {attempts} attempts: {last_error}", "send_failed")


def measure_parallel_session_scalability(max_sessions: int, test_duration_seconds: int) -> Dict[str, Any]:
    """Measure scalability of parallel session operations.
    
    Args:
        max_sessions: Maximum number of sessions to test
        test_duration_seconds: Duration of the test
        
    Returns:
        Dict with scalability metrics
    """
    try:
        start_time = time.time()
        created_sessions = []
        metrics = {
            "sessions_created": 0,
            "sessions_failed": 0,
            "avg_creation_time_ms": 0,
            "total_time_seconds": 0
        }
        
        creation_times = []
        
        # Create sessions up to max or until timeout
        for i in range(max_sessions):
            if time.time() - start_time > test_duration_seconds:
                break
            
            session_name = f"scale-test-{i}"
            creation_start = time.time()
            
            result = subprocess.run(
                ['tmux', 'new-session', '-d', '-s', session_name],
                capture_output=True,
                check=False
            )
            
            creation_time_ms = (time.time() - creation_start) * 1000
            creation_times.append(creation_time_ms)
            
            if result.returncode == 0:
                created_sessions.append(session_name)
                metrics["sessions_created"] += 1
            else:
                metrics["sessions_failed"] += 1
        
        # Clean up created sessions
        for session in created_sessions:
            subprocess.run(
                ['tmux', 'kill-session', '-t', session],
                capture_output=True,
                check=False
            )
        
        # Calculate metrics
        metrics["total_time_seconds"] = time.time() - start_time
        metrics["avg_creation_time_ms"] = (
            sum(creation_times) / len(creation_times)
            if creation_times else 0
        )
        
        return _ok({
            "scalability_metrics": metrics,
            "max_tested": metrics["sessions_created"],
            "success_rate": (
                metrics["sessions_created"] / (metrics["sessions_created"] + metrics["sessions_failed"])
                if (metrics["sessions_created"] + metrics["sessions_failed"]) > 0 else 0
            )
        })
        
    except Exception as e:
        return _err(f"Failed to measure scalability: {str(e)}", "scalability_error")