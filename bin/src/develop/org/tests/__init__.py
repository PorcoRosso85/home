"""Test package for org project.

This package contains all tests for the org project following TDD principles.
Tests are organized by module and include both unit and integration tests.

Test Structure:
- test_infrastructure.py: Tests for tmux connection and infrastructure layer
- test_infrastructure_windows.py: Tests for window management functions

Test Categories:
- Unit tests: Fast, isolated tests of individual components
- Integration tests: Tests that verify component interactions
- Tmux tests: Tests that require actual tmux connection

Usage:
    pytest                    # Run all tests
    pytest -m unit           # Run only unit tests
    pytest -m integration    # Run only integration tests
    pytest -m tmux           # Run only tmux-dependent tests
    pytest --cov            # Run with coverage report
"""

__version__ = "0.1.0"
__author__ = "Org Project"