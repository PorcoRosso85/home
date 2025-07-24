"""Infrastructure layer for log module - handles external I/O dependencies."""

from typing import Any


def stdout_writer(message: str) -> None:
    """
    Write a message to stdout.
    
    This function wraps the print functionality to isolate the external
    dependency of stdout output. It provides a single point of control
    for how log messages are output to the console.
    
    Args:
        message: The message to write to stdout
        
    Note:
        This abstraction allows for future extensibility such as:
        - Adding timestamps
        - Formatting output
        - Redirecting to different outputs
        - Buffering messages
    """
    print(message)