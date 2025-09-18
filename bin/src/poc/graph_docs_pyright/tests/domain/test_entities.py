"""Tests for domain entities: Symbol, Diagnostic, and FileAnalysis.

These tests follow the TDD philosophy - they define the behavior and specifications
of our domain entities before implementation exists.
"""

import pytest
from pathlib import Path
from graph_docs.domain.entities import Symbol, Diagnostic, FileAnalysis, DiagnosticSeverity


class TestSymbol:
    """Tests for Symbol value object representing a code symbol."""
    
    def test_symbol_creation_with_valid_data(self):
        """Symbol should be created with name, kind, and location."""
        symbol = Symbol(
            name="hello",
            kind="function",
            start_line=1,
            start_column=0,
            end_line=3,
            end_column=4
        )
        
        assert symbol.name == "hello"
        assert symbol.kind == "function"
        assert symbol.start_line == 1
        assert symbol.start_column == 0
        assert symbol.end_line == 3
        assert symbol.end_column == 4
    
    def test_symbol_equality(self):
        """Symbols with same data should be equal."""
        symbol1 = Symbol(
            name="test_func",
            kind="function",
            start_line=10,
            start_column=0,
            end_line=15,
            end_column=0
        )
        
        symbol2 = Symbol(
            name="test_func",
            kind="function",
            start_line=10,
            start_column=0,
            end_line=15,
            end_column=0
        )
        
        assert symbol1 == symbol2
    
    def test_symbol_inequality(self):
        """Symbols with different data should not be equal."""
        symbol1 = Symbol(
            name="func1",
            kind="function",
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=0
        )
        
        symbol2 = Symbol(
            name="func2",
            kind="function",
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=0
        )
        
        assert symbol1 != symbol2
    
    @pytest.mark.parametrize("invalid_line,invalid_column", [
        (-1, 0),   # negative line
        (0, -1),   # negative column
        (10, 0),   # end_line < start_line (when end_line=5)
    ])
    def test_symbol_validates_position(self, invalid_line, invalid_column):
        """Symbol should validate that positions are non-negative and end >= start."""
        with pytest.raises(ValueError):
            if invalid_line < 0:
                Symbol(
                    name="test",
                    kind="function",
                    start_line=invalid_line,
                    start_column=0,
                    end_line=5,
                    end_column=0
                )
            elif invalid_column < 0:
                Symbol(
                    name="test",
                    kind="function",
                    start_line=1,
                    start_column=invalid_column,
                    end_line=5,
                    end_column=0
                )
            else:  # end < start case
                Symbol(
                    name="test",
                    kind="function",
                    start_line=invalid_line,
                    start_column=0,
                    end_line=5,
                    end_column=0
                )


class TestDiagnostic:
    """Tests for Diagnostic value object representing a code issue."""
    
    def test_diagnostic_creation_with_valid_data(self):
        """Diagnostic should be created with message, severity, and location."""
        diagnostic = Diagnostic(
            message="Type error: expected int, got str",
            severity=DiagnosticSeverity.ERROR,
            start_line=10,
            start_column=5,
            end_line=10,
            end_column=15,
            rule="type-mismatch"
        )
        
        assert diagnostic.message == "Type error: expected int, got str"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert diagnostic.start_line == 10
        assert diagnostic.start_column == 5
        assert diagnostic.end_line == 10
        assert diagnostic.end_column == 15
        assert diagnostic.rule == "type-mismatch"
    
    def test_diagnostic_without_rule(self):
        """Diagnostic should allow optional rule parameter."""
        diagnostic = Diagnostic(
            message="Unused variable 'x'",
            severity=DiagnosticSeverity.WARNING,
            start_line=5,
            start_column=0,
            end_line=5,
            end_column=1
        )
        
        assert diagnostic.rule is None
    
    @pytest.mark.parametrize("severity,expected_string", [
        (DiagnosticSeverity.ERROR, "error"),
        (DiagnosticSeverity.WARNING, "warning"),
        (DiagnosticSeverity.INFORMATION, "information"),
        (DiagnosticSeverity.HINT, "hint"),
    ])
    def test_diagnostic_severity_string_representation(self, severity, expected_string):
        """DiagnosticSeverity should have string representation."""
        assert severity.value == expected_string
    
    def test_diagnostic_is_error_property(self):
        """Diagnostic should have is_error property."""
        error_diagnostic = Diagnostic(
            message="Error",
            severity=DiagnosticSeverity.ERROR,
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=1
        )
        
        warning_diagnostic = Diagnostic(
            message="Warning",
            severity=DiagnosticSeverity.WARNING,
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=1
        )
        
        assert error_diagnostic.is_error is True
        assert warning_diagnostic.is_error is False
    
    def test_diagnostic_validates_empty_message(self):
        """Diagnostic should not allow empty message."""
        with pytest.raises(ValueError, match="message cannot be empty"):
            Diagnostic(
                message="",
                severity=DiagnosticSeverity.ERROR,
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=1
            )


class TestFileAnalysis:
    """Tests for FileAnalysis entity representing analysis results for a file."""
    
    def test_file_analysis_creation(self):
        """FileAnalysis should be created with file path, symbols, and diagnostics."""
        symbols = [
            Symbol(
                name="main",
                kind="function",
                start_line=1,
                start_column=0,
                end_line=5,
                end_column=0
            )
        ]
        
        diagnostics = [
            Diagnostic(
                message="Unused import",
                severity=DiagnosticSeverity.WARNING,
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=10
            )
        ]
        
        file_analysis = FileAnalysis(
            file_path=Path("/test/example.py"),
            symbols=symbols,
            diagnostics=diagnostics
        )
        
        assert file_analysis.file_path == Path("/test/example.py")
        assert len(file_analysis.symbols) == 1
        assert len(file_analysis.diagnostics) == 1
        assert file_analysis.symbols[0].name == "main"
        assert file_analysis.diagnostics[0].message == "Unused import"
    
    def test_file_analysis_empty_collections(self):
        """FileAnalysis should handle empty symbols and diagnostics."""
        file_analysis = FileAnalysis(
            file_path=Path("/test/clean.py"),
            symbols=[],
            diagnostics=[]
        )
        
        assert len(file_analysis.symbols) == 0
        assert len(file_analysis.diagnostics) == 0
    
    def test_file_analysis_error_count(self):
        """FileAnalysis should count error diagnostics."""
        diagnostics = [
            Diagnostic(
                message="Type error",
                severity=DiagnosticSeverity.ERROR,
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=1
            ),
            Diagnostic(
                message="Another error",
                severity=DiagnosticSeverity.ERROR,
                start_line=2,
                start_column=0,
                end_line=2,
                end_column=1
            ),
            Diagnostic(
                message="Warning",
                severity=DiagnosticSeverity.WARNING,
                start_line=3,
                start_column=0,
                end_line=3,
                end_column=1
            )
        ]
        
        file_analysis = FileAnalysis(
            file_path=Path("/test/errors.py"),
            symbols=[],
            diagnostics=diagnostics
        )
        
        assert file_analysis.error_count == 2
    
    def test_file_analysis_warning_count(self):
        """FileAnalysis should count warning diagnostics."""
        diagnostics = [
            Diagnostic(
                message="Warning 1",
                severity=DiagnosticSeverity.WARNING,
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=1
            ),
            Diagnostic(
                message="Warning 2",
                severity=DiagnosticSeverity.WARNING,
                start_line=2,
                start_column=0,
                end_line=2,
                end_column=1
            ),
            Diagnostic(
                message="Info",
                severity=DiagnosticSeverity.INFORMATION,
                start_line=3,
                start_column=0,
                end_line=3,
                end_column=1
            )
        ]
        
        file_analysis = FileAnalysis(
            file_path=Path("/test/warnings.py"),
            symbols=[],
            diagnostics=diagnostics
        )
        
        assert file_analysis.warning_count == 2
    
    def test_file_analysis_has_issues_property(self):
        """FileAnalysis should indicate if it has any diagnostics."""
        clean_analysis = FileAnalysis(
            file_path=Path("/test/clean.py"),
            symbols=[],
            diagnostics=[]
        )
        
        with_issues_analysis = FileAnalysis(
            file_path=Path("/test/issues.py"),
            symbols=[],
            diagnostics=[
                Diagnostic(
                    message="Issue",
                    severity=DiagnosticSeverity.WARNING,
                    start_line=1,
                    start_column=0,
                    end_line=1,
                    end_column=1
                )
            ]
        )
        
        assert clean_analysis.has_issues is False
        assert with_issues_analysis.has_issues is True
    
    def test_file_analysis_symbols_by_kind(self):
        """FileAnalysis should filter symbols by kind."""
        symbols = [
            Symbol(name="MyClass", kind="class", start_line=1, start_column=0, end_line=10, end_column=0),
            Symbol(name="method1", kind="function", start_line=2, start_column=4, end_line=5, end_column=4),
            Symbol(name="method2", kind="function", start_line=6, start_column=4, end_line=9, end_column=4),
            Symbol(name="CONSTANT", kind="variable", start_line=11, start_column=0, end_line=11, end_column=20),
        ]
        
        file_analysis = FileAnalysis(
            file_path=Path("/test/example.py"),
            symbols=symbols,
            diagnostics=[]
        )
        
        functions = file_analysis.get_symbols_by_kind("function")
        assert len(functions) == 2
        assert all(s.kind == "function" for s in functions)
        assert {s.name for s in functions} == {"method1", "method2"}
        
        classes = file_analysis.get_symbols_by_kind("class")
        assert len(classes) == 1
        assert classes[0].name == "MyClass"