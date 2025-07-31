import time
import pytest

def test_quick():
    """This test completes quickly"""
    assert 1 + 1 == 2

def test_slow_but_ok():
    """This test is slow but within timeout"""
    time.sleep(1)
    assert True

@pytest.mark.timeout(2)
def test_with_explicit_timeout():
    """This test has explicit 2 second timeout"""
    time.sleep(1)
    assert True

@pytest.mark.timeout(1)
def test_will_timeout():
    """This test will timeout after 1 second"""
    time.sleep(3)  # This will cause timeout
    assert True

def test_infinite_loop():
    """This test has an infinite loop"""
    while True:
        pass