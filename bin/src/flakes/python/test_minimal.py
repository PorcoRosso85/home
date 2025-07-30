def test_pass():
    """This test always passes"""
    assert 1 + 1 == 2

def test_fail():
    """This test always fails"""
    assert 1 + 1 == 3

def test_skip():
    """This test is skipped"""
    import pytest
    pytest.skip("Skipping this test for demo")

def test_with_output():
    """This test prints to stdout"""
    print("Hello from test!")
    print("This is stdout output")
    assert True