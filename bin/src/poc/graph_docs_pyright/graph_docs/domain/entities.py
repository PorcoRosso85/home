"""Domain entities for graph_docs Pyright analysis.

This module contains the core domain entities that represent the analysis results
from Pyright. These are pure domain objects with no external dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Any, Dict, TypedDict


class DiagnosticSeverity(Enum):
    """Diagnostic severity levels matching LSP specification."""
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"
    HINT = "hint"


@dataclass(frozen=True)
class Symbol:
    """Value object representing a code symbol (function, class, variable, etc.)."""
    
    name: str
    kind: str  # function, class, method, variable, etc.
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    
    def __post_init__(self):
        """Validate symbol data."""
        if self.start_line < 0:
            raise ValueError("start_line must be non-negative")
        if self.start_column < 0:
            raise ValueError("start_column must be non-negative")
        if self.end_line < 0:
            raise ValueError("end_line must be non-negative")
        if self.end_column < 0:
            raise ValueError("end_column must be non-negative")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        if self.end_line == self.start_line and self.end_column < self.start_column:
            raise ValueError("end_column must be >= start_column when on same line")


@dataclass(frozen=True)
class Diagnostic:
    """Value object representing a diagnostic (error, warning, etc.) from Pyright."""
    
    message: str
    severity: DiagnosticSeverity
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    rule: Optional[str] = None
    
    def __post_init__(self):
        """Validate diagnostic data."""
        if not self.message.strip():
            raise ValueError("message cannot be empty")
        if self.start_line < 0:
            raise ValueError("start_line must be non-negative")
        if self.start_column < 0:
            raise ValueError("start_column must be non-negative")
        if self.end_line < 0:
            raise ValueError("end_line must be non-negative")
        if self.end_column < 0:
            raise ValueError("end_column must be non-negative")
    
    @property
    def is_error(self) -> bool:
        """Check if this diagnostic is an error."""
        return self.severity == DiagnosticSeverity.ERROR


@dataclass
class FileAnalysis:
    """Entity representing the analysis results for a single file."""
    
    file_path: Path
    symbols: List[Symbol]
    diagnostics: List[Diagnostic]
    
    @property
    def error_count(self) -> int:
        """Count of error-level diagnostics."""
        return sum(1 for d in self.diagnostics if d.is_error)
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level diagnostics."""
        return sum(1 for d in self.diagnostics if d.severity == DiagnosticSeverity.WARNING)
    
    @property
    def has_issues(self) -> bool:
        """Check if this file has any diagnostics."""
        return len(self.diagnostics) > 0
    
    def get_symbols_by_kind(self, kind: str) -> List[Symbol]:
        """Get all symbols of a specific kind."""
        return [s for s in self.symbols if s.kind == kind]


# Dual KuzuDB Domain Entities

class ErrorDict(TypedDict):
    """エラー情報を表す型"""
    error: str
    details: Optional[str]


class InitResult(TypedDict):
    """init_local_db()の成功結果を表す型"""
    success: bool
    message: str


class ConnectResult(TypedDict):
    """connect()の成功結果を表す型"""
    success: bool
    message: str


@dataclass
class QueryResult:
    """クエリ実行結果"""
    source: str  # "db1" or "db2"
    columns: List[str]
    rows: List[List[Any]]
    error: Optional[str] = None


@dataclass
class DualQueryResult:
    """2つのDBに対するクエリ結果"""
    db1_result: Optional[QueryResult]
    db2_result: Optional[QueryResult]
    combined: Optional[List[Dict[str, Any]]] = None