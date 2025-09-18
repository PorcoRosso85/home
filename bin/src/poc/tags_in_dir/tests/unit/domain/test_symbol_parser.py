"""Unit tests for symbol parser functions."""

import pytest
from pathlib import Path
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.domain.symbol_parser import (
    parse_ctags_output,
    extract_line_number,
    filter_symbols_by_kind,
    filter_symbols_by_file
)
from src.domain.symbol import Symbol


class TestExtractLineNumber:
    """Test extract_line_number function."""
    
    def test_extract_direct_line_number(self):
        """Test extracting a direct line number."""
        assert extract_line_number("42") == 42
        assert extract_line_number("123") == 123
        assert extract_line_number("1") == 1
    
    def test_extract_line_number_with_suffix(self):
        """Test extracting line number with ;" suffix."""
        assert extract_line_number('42;"') == 42
        assert extract_line_number('123;"') == 123
        assert extract_line_number('1;"') == 1
    
    def test_extract_line_number_with_spaces(self):
        """Test extracting line number with surrounding spaces."""
        assert extract_line_number(' 42 ;"') == 42
        assert extract_line_number('  123  ;"') == 123
    
    def test_extract_regex_pattern_returns_none(self):
        """Test that regex patterns return None."""
        assert extract_line_number('/^def function(/:') is None
        assert extract_line_number('/^class MyClass/:') is None
        assert extract_line_number('/^    return value/') is None
    
    def test_extract_invalid_patterns(self):
        """Test that invalid patterns return None."""
        assert extract_line_number('abc') is None
        assert extract_line_number('') is None
        assert extract_line_number(';"') is None
        assert extract_line_number('12abc;"') is None


class TestParseCtagsOutput:
    """Test parse_ctags_output function."""
    
    def test_parse_empty_output(self):
        """Test parsing empty ctags output."""
        assert parse_ctags_output("", "/base/path") == []
        assert parse_ctags_output("   ", "/base/path") == []
        assert parse_ctags_output("\n\n", "/base/path") == []
    
    def test_parse_header_comments(self):
        """Test parsing output with header comments."""
        ctags_output = """!_TAG_FILE_FORMAT	2	/extended format/
!_TAG_FILE_SORTED	1	/0=unsorted, 1=sorted/
!_TAG_PROGRAM_NAME	Universal Ctags	//
MyClass	file.py	10;"	c
method	file.py	15;"	m	scope:class:MyClass"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 2
        assert all(not s.name.startswith('!') for s in symbols)
    
    def test_parse_standard_output(self):
        """Test parsing standard ctags output."""
        ctags_output = """function_one	module.py	42;"	f
ClassTwo	module.py	100;"	c
method_three	module.py	105;"	m	scope:class:ClassTwo	signature:(self, arg1, arg2)"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 3
        
        # Check first symbol
        assert symbols[0].name == "function_one"
        assert symbols[0].kind == "f"
        assert symbols[0].location_uri.endswith("module.py#L42")
        assert symbols[0].scope is None
        
        # Check third symbol with scope and signature
        assert symbols[2].name == "method_three"
        assert symbols[2].kind == "m"
        assert symbols[2].scope == "class:ClassTwo"
        assert symbols[2].signature == "(self, arg1, arg2)"
    
    def test_parse_absolute_paths(self):
        """Test parsing with absolute file paths."""
        ctags_output = """function	/absolute/path/file.py	20;"	f"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 1
        assert symbols[0].location_uri == "file:///absolute/path/file.py#L20"
    
    def test_parse_relative_paths(self):
        """Test parsing with relative file paths."""
        ctags_output = """function	relative/file.py	30;"	f"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 1
        assert "/base/path/relative/file.py#L30" in symbols[0].location_uri
    
    def test_skip_malformed_lines(self):
        """Test that malformed lines are skipped."""
        ctags_output = """good_function	file.py	10;"	f
malformed_line_too_few_fields
another_good	file.py	20;"	f
name	file	pattern_without_number	kind
final_good	file.py	30;"	f"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 3
        assert [s.name for s in symbols] == ["good_function", "another_good", "final_good"]
    
    def test_parse_various_symbol_kinds(self):
        """Test parsing various symbol kinds."""
        ctags_output = """MyClass	file.py	10;"	c
function	file.py	20;"	f
method	file.py	30;"	m	scope:class:MyClass
variable	file.py	40;"	v
constant	file.py	50;"	C
module	file.py	1;"	M
import	file.py	5;"	i"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 7
        kinds = [s.kind for s in symbols]
        assert set(kinds) == {"c", "f", "m", "v", "C", "M", "i"}
    
    def test_parse_with_multiple_extended_fields(self):
        """Test parsing lines with multiple extended fields."""
        ctags_output = """method	file.py	100;"	m	scope:class:MyClass	signature:(self, x, y)	access:public
function	file.py	200;"	f	signature:(a, b, c)	returns:int"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 2
        assert symbols[0].scope == "class:MyClass"
        assert symbols[0].signature == "(self, x, y)"
        assert symbols[1].signature == "(a, b, c)"
    
    def test_parse_special_characters_in_names(self):
        """Test parsing symbols with special characters."""
        ctags_output = """__init__	file.py	10;"	m	scope:class:MyClass
_private_var	file.py	20;"	v
test-function	file.py	30;"	f
var$special	file.py	40;"	v"""
        
        symbols = parse_ctags_output(ctags_output, "/base/path")
        assert len(symbols) == 4
        assert symbols[0].name == "__init__"
        assert symbols[1].name == "_private_var"
        assert symbols[2].name == "test-function"
        assert symbols[3].name == "var$special"
    
    def test_parse_invalid_symbol_returns_error(self):
        """Test that invalid symbol data returns an error."""
        # Create ctags output that would cause Symbol validation to fail
        # Since Symbol requires specific fields, we need to check the Symbol class
        # For now, let's assume empty name would be invalid
        ctags_output = """	file.py	10;"	f"""
        
        result = parse_ctags_output(ctags_output, "/base/path")
        # If Symbol validation fails, we expect an error dict
        if isinstance(result, dict) and "error" in result:
            assert result["error"]["code"] == "SYMBOL_VALIDATION_ERROR"
        else:
            # If no validation error, we should have skipped the malformed line
            assert len(result) == 0


class TestFilterSymbolsByKind:
    """Test filter_symbols_by_kind function."""
    
    def test_filter_single_kind(self):
        """Test filtering by a single kind."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file://test#L1"),
            Symbol(name="class1", kind="c", location_uri="file://test#L2"),
            Symbol(name="func2", kind="f", location_uri="file://test#L3"),
            Symbol(name="method1", kind="m", location_uri="file://test#L4"),
        ]
        
        filtered = filter_symbols_by_kind(symbols, ["f"])
        assert len(filtered) == 2
        assert all(s.kind == "f" for s in filtered)
        assert [s.name for s in filtered] == ["func1", "func2"]
    
    def test_filter_multiple_kinds(self):
        """Test filtering by multiple kinds."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file://test#L1"),
            Symbol(name="class1", kind="c", location_uri="file://test#L2"),
            Symbol(name="func2", kind="f", location_uri="file://test#L3"),
            Symbol(name="method1", kind="m", location_uri="file://test#L4"),
        ]
        
        filtered = filter_symbols_by_kind(symbols, ["f", "c"])
        assert len(filtered) == 3
        assert set(s.kind for s in filtered) == {"f", "c"}
    
    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file://test#L1"),
            Symbol(name="class1", kind="c", location_uri="file://test#L2"),
        ]
        
        filtered = filter_symbols_by_kind(symbols, ["m", "v"])
        assert len(filtered) == 0
    
    def test_filter_empty_symbols(self):
        """Test filtering empty symbol list."""
        filtered = filter_symbols_by_kind([], ["f", "c"])
        assert filtered == []
    
    def test_filter_empty_kinds(self):
        """Test filtering with empty kinds list."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file://test#L1"),
            Symbol(name="class1", kind="c", location_uri="file://test#L2"),
        ]
        
        filtered = filter_symbols_by_kind(symbols, [])
        assert len(filtered) == 0


class TestFilterSymbolsByFile:
    """Test filter_symbols_by_file function."""
    
    def test_filter_by_file_path(self):
        """Test filtering symbols by file path."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file:///path/to/file1.py#L10"),
            Symbol(name="func2", kind="f", location_uri="file:///path/to/file2.py#L20"),
            Symbol(name="func3", kind="f", location_uri="file:///path/to/file1.py#L30"),
            Symbol(name="func4", kind="f", location_uri="file:///other/file.py#L40"),
        ]
        
        filtered = filter_symbols_by_file(symbols, "/path/to/file1.py")
        assert len(filtered) == 2
        assert all("file1.py" in s.location_uri for s in filtered)
        assert [s.name for s in filtered] == ["func1", "func3"]
    
    def test_filter_relative_path(self):
        """Test filtering with relative path (gets resolved)."""
        # This test depends on the current working directory
        # We'll create symbols with absolute paths and filter with relative
        cwd = Path.cwd()
        test_file = cwd / "test.py"
        
        symbols = [
            Symbol(name="func1", kind="f", location_uri=f"file://{test_file}#L10"),
            Symbol(name="func2", kind="f", location_uri="file:///other/path/test.py#L20"),
            Symbol(name="func3", kind="f", location_uri=f"file://{test_file}#L30"),
        ]
        
        filtered = filter_symbols_by_file(symbols, "test.py")
        # Should match based on resolved absolute path
        assert len(filtered) == 2
        assert [s.name for s in filtered] == ["func1", "func3"]
    
    def test_filter_no_matches(self):
        """Test filtering with no matching file."""
        symbols = [
            Symbol(name="func1", kind="f", location_uri="file:///path/to/file1.py#L10"),
            Symbol(name="func2", kind="f", location_uri="file:///path/to/file2.py#L20"),
        ]
        
        filtered = filter_symbols_by_file(symbols, "/nonexistent/file.py")
        assert len(filtered) == 0
    
    def test_filter_empty_symbols(self):
        """Test filtering empty symbol list."""
        filtered = filter_symbols_by_file([], "/any/file.py")
        assert filtered == []


class TestRealWorldCtagsOutput:
    """Test with real-world ctags output samples."""
    
    def test_python_ctags_output(self):
        """Test parsing Python ctags output."""
        ctags_output = """!_TAG_FILE_FORMAT	2	/extended format; --format=1 will not append ;" to lines/
!_TAG_FILE_SORTED	1	/0=unsorted, 1=sorted, 2=foldcase/
!_TAG_OUTPUT_MODE	u-ctags	/u-ctags or e-ctags/
!_TAG_PROGRAM_AUTHOR	Universal Ctags Team	//
!_TAG_PROGRAM_NAME	Universal Ctags	/Derived from Exuberant Ctags/
!_TAG_PROGRAM_URL	https://ctags.io/	/official site/
!_TAG_PROGRAM_VERSION	0.0.0	//
Config	app/config.py	8;"	c
DatabaseConfig	app/config.py	15;"	c	scope:class:Config
__init__	app/models.py	12;"	m	scope:class:User	signature:(self, name, email)
create_app	app/__init__.py	10;"	f	signature:()
get_db_url	app/config.py	20;"	m	scope:class:DatabaseConfig	signature:(self)
logger	app/utils.py	5;"	v
setup_logging	app/utils.py	8;"	f	signature:(level=INFO)"""
        
        symbols = parse_ctags_output(ctags_output, "/project")
        
        # Should skip all header lines
        assert len(symbols) == 7
        
        # Check various symbols
        config_symbol = next(s for s in symbols if s.name == "Config")
        assert config_symbol.kind == "c"
        assert config_symbol.location_uri.endswith("app/config.py#L8")
        
        init_symbol = next(s for s in symbols if s.name == "__init__")
        assert init_symbol.kind == "m"
        assert init_symbol.scope == "class:User"
        assert init_symbol.signature == "(self, name, email)"
        
        logger_symbol = next(s for s in symbols if s.name == "logger")
        assert logger_symbol.kind == "v"
    
    def test_javascript_ctags_output(self):
        """Test parsing JavaScript ctags output."""
        ctags_output = """Arrow	src/components.js	15;"	f	signature:() => console.log('arrow')
Component	src/components.js	5;"	c
MyClass	src/index.js	10;"	c
constructor	src/index.js	11;"	m	scope:class:MyClass	signature:(props)
export	src/utils.js	25;"	v
handleClick	src/components.js	8;"	m	scope:class:Component	signature:(event)
render	src/components.js	12;"	m	scope:class:Component	signature:()"""
        
        symbols = parse_ctags_output(ctags_output, "/webapp")
        assert len(symbols) == 7
        
        # Check arrow function
        arrow = next(s for s in symbols if s.name == "Arrow")
        assert arrow.signature == "() => console.log('arrow')"
        
        # Check class methods
        methods = [s for s in symbols if s.kind == "m"]
        assert len(methods) == 3
        assert all(m.scope is not None for m in methods)