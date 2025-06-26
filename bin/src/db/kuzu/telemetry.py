"""Minimal telemetry module for KuzuDB connection."""

def log(level: str, component: str, message: str, **kwargs):
    """Log a message with context."""
    # Minimal implementation - just print for now
    context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    print(f"[{level}] {component}: {message} {context}".strip())


# In-source test
def test_log_基本出力_フォーマットされる():
    """log_基本メッセージ_正しくフォーマットされる"""
    import io
    import sys
    from contextlib import redirect_stdout
    
    # Arrange
    f = io.StringIO()
    
    # Act
    with redirect_stdout(f):
        log('INFO', 'test.component', 'Test message', key1='value1', key2='value2')
    
    # Assert
    output = f.getvalue().strip()
    assert '[INFO]' in output
    assert 'test.component' in output
    assert 'Test message' in output
    assert 'key1=value1' in output
    assert 'key2=value2' in output


if __name__ == "__main__":
    test_log_基本出力_フォーマットされる()
    print("✓ test_log_基本出力_フォーマットされる")