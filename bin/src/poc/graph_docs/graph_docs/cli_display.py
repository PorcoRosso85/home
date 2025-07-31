#!/usr/bin/env python3
"""CLI Display Utility with Structured Logging

This module provides display functions that maintain user-facing output
while using structured logging internally for debugging and tracing.
"""

import os
import sys
import json
import logging
from typing import List, Optional, Dict, Any, Tuple, Union

__all__ = [
    'error',
    'info',
    'table',
    'json_output',
    'query_result',
    'dual_query_info',
    'database_info',
    'section_title',
    'newline',
    'combined_results',
]

# Set up structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create formatter for structured logs
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add file handler for debug logs
log_file = os.environ.get('GRAPH_DOCS_LOG_FILE')
if log_file:
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError):
        # Ignore file logging errors in read-only environments
        pass

# Check if we're in display mode or log-only mode
DISPLAY_MODE = os.environ.get('GRAPH_DOCS_DISPLAY_MODE', 'true').lower() == 'true'


class CLIDisplay:
    """CLI Display utility that provides structured logging with optional display output"""
    
    def __init__(self, display_mode: bool = None):
        """Initialize the display utility
        
        Args:
            display_mode: Override the global DISPLAY_MODE setting. 
                         If None, uses environment variable.
        """
        self.display_mode = display_mode if display_mode is not None else DISPLAY_MODE
        logger.debug(f"CLIDisplay initialized with display_mode={self.display_mode}")
    
    def _output(self, content: str, file=None) -> None:
        """Internal method to handle output with logging
        
        Args:
            content: The content to output
            file: The file to write to (default: stdout)
        """
        if file is None:
            file = sys.stdout
        
        # Always log the output
        log_level = logging.ERROR if file == sys.stderr else logging.INFO
        logger.log(log_level, f"OUTPUT: {content}")
        
        # Only display if in display mode
        if self.display_mode:
            print(content, file=file)
    
    def error(self, message: str) -> None:
        """Display an error message to stderr
        
        Args:
            message: The error message to display
        """
        logger.error(f"ERROR_OUTPUT: {message}")
        self._output(message, file=sys.stderr)
    
    def info(self, message: str) -> None:
        """Display an info message to stdout
        
        Args:
            message: The info message to display
        """
        logger.info(f"INFO_OUTPUT: {message}")
        self._output(message)
    
    def table(self, 
              title: str,
              columns: Optional[List[str]],
              rows: List[List[Any]],
              separator_width: int = 50) -> None:
        """Display data in a simple table format
        
        Args:
            title: The title for the table
            columns: Column headers (optional)
            rows: Data rows
            separator_width: Width of separator lines
        """
        logger.debug(f"Displaying table: title='{title}', columns={columns}, row_count={len(rows)}")
        
        # Title
        self._output(f"\n{title}:")
        self._output("-" * separator_width)
        
        # Header
        if columns:
            self._output(" | ".join(columns))
            self._output("-" * separator_width)
            logger.debug(f"Table columns: {columns}")
        
        # Data rows
        for i, row in enumerate(rows):
            row_str = " | ".join(str(val) for val in row)
            self._output(row_str)
            logger.debug(f"Table row {i}: {row}")
    
    def json_output(self, data: Dict[Any, Any], indent: int = 2) -> None:
        """Display data in JSON format
        
        Args:
            data: The data to display as JSON
            indent: Number of spaces for indentation
        """
        logger.debug(f"Displaying JSON: {json.dumps(data, indent=None)}")
        json_str = json.dumps(data, indent=indent)
        self._output(json_str)
    
    def query_result(self, 
                     source: str,
                     columns: Optional[List[str]],
                     rows: List[List[Any]],
                     error: Optional[str] = None) -> None:
        """Display a query result in table format
        
        Args:
            source: The source database name
            columns: Column headers
            rows: Result rows
            error: Error message if query failed
        """
        logger.debug(f"Displaying query result: source='{source}', error={error is not None}")
        
        if error:
            self.error(f"Error in {source}: {error}")
            return
        
        if not rows:
            self._output(f"{source}: No results")
            logger.debug(f"Query result for {source}: empty result set")
            return
        
        logger.debug(f"Query result for {source}: {len(rows)} rows")
        self.table(f"{source} Results", columns, rows)
    
    def dual_query_info(self, db1_query: str, db2_query: str) -> None:
        """Display information about dual queries
        
        Args:
            db1_query: Query for DB1
            db2_query: Query for DB2
        """
        logger.debug(f"Dual query info: db1='{db1_query}', db2='{db2_query}'")
        self._output(f"DB1 Query: {db1_query}")
        self._output(f"DB2 Query: {db2_query}\n")
    
    def database_info(self, db1_path: str, db2_path: str) -> None:
        """Display database information header
        
        Args:
            db1_path: Path to DB1
            db2_path: Path to DB2
        """
        logger.debug(f"Database info: db1='{db1_path}', db2='{db2_path}'")
        self._output("Database Information:\n")
        self._output(f"DB1 Path: {db1_path}")
        self._output(f"DB2 Path: {db2_path}")
    
    def section_title(self, title: str) -> None:
        """Display a section title
        
        Args:
            title: The section title
        """
        logger.debug(f"Section title: '{title}'")
        self._output(f"\n{title}:")
    
    def newline(self) -> None:
        """Display a blank line"""
        logger.debug("Outputting blank line")
        self._output("")
    
    def combined_results(self, data: Dict[Any, Any]) -> None:
        """Display combined results section
        
        Args:
            data: Combined results data
        """
        logger.debug(f"Displaying combined results: {data}")
        self._output("\nCombined Results:")
        self.json_output(data)


# Global instance for convenience
display = CLIDisplay()


# Convenience functions that use the global instance
def error(message: str) -> None:
    """Display an error message"""
    display.error(message)


def info(message: str) -> None:
    """Display an info message"""
    display.info(message)


def table(title: str, columns: Optional[List[str]], rows: List[List[Any]], 
          separator_width: int = 50) -> None:
    """Display data in table format"""
    display.table(title, columns, rows, separator_width)


def json_output(data: Dict[Any, Any], indent: int = 2) -> None:
    """Display data as JSON"""
    display.json_output(data, indent)


def query_result(source: str, columns: Optional[List[str]], 
                 rows: List[List[Any]], error: Optional[str] = None) -> None:
    """Display a query result"""
    display.query_result(source, columns, rows, error)


def dual_query_info(db1_query: str, db2_query: str) -> None:
    """Display dual query information"""
    display.dual_query_info(db1_query, db2_query)


def database_info(db1_path: str, db2_path: str) -> None:
    """Display database information"""
    display.database_info(db1_path, db2_path)


def section_title(title: str) -> None:
    """Display a section title"""
    display.section_title(title)


def newline() -> None:
    """Display a blank line"""
    display.newline()


def combined_results(data: Dict[Any, Any]) -> None:
    """Display combined results"""
    display.combined_results(data)