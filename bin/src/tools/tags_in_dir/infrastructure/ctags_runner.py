"""Infrastructure for running ctags subprocess."""

import subprocess
from typing import List, Union, Optional
from pathlib import Path
from ..domain.errors import ErrorDict, create_error


def run_ctags(
    path: str,
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[str, ErrorDict]:
    """
    Run ctags on a directory or file.
    
    Args:
        path: Directory or file path to analyze
        extensions: List of file extensions to include (e.g., [".py", ".js"])
        ctags_path: Path to ctags executable
        
    Returns:
        ctags output string or error dictionary
    """
    abs_path = Path(path).resolve()
    
    if not abs_path.exists():
        return create_error(
            "PATH_NOT_FOUND",
            f"Path does not exist: {abs_path}",
            {"path": str(abs_path)}
        )
    
    # Build ctags command
    cmd = [
        ctags_path,
        '--output-format=json',
        '--fields=+KZlnsSt',
        '--extras=+q',
        '--recurse=yes' if abs_path.is_dir() else '--recurse=no',
        str(abs_path)
    ]
    
    # Add language filters if extensions provided
    if extensions:
        for ext in extensions:
            # Map extensions to ctags language names
            lang = map_extension_to_language(ext)
            if lang:
                cmd.extend(['--languages=' + lang])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return create_error(
                "CTAGS_EXECUTION_ERROR",
                f"ctags failed with return code {result.returncode}",
                {
                    "stderr": result.stderr,
                    "command": ' '.join(cmd)
                }
            )
            
        return result.stdout
        
    except FileNotFoundError:
        return create_error(
            "CTAGS_NOT_FOUND",
            "ctags executable not found. Please install Universal Ctags.",
            {"ctags_path": ctags_path}
        )
    except Exception as e:
        return create_error(
            "CTAGS_UNKNOWN_ERROR",
            f"Unexpected error running ctags: {str(e)}",
            {"command": ' '.join(cmd)}
        )


def run_ctags_standard_format(
    path: str,
    extensions: Optional[List[str]] = None,
    ctags_path: str = "ctags"
) -> Union[str, ErrorDict]:
    """
    Run ctags with standard format output.
    
    Args:
        path: Directory or file path to analyze
        extensions: List of file extensions to include
        ctags_path: Path to ctags executable
        
    Returns:
        ctags output string or error dictionary
    """
    abs_path = Path(path).resolve()
    
    if not abs_path.exists():
        return create_error(
            "PATH_NOT_FOUND",
            f"Path does not exist: {abs_path}",
            {"path": str(abs_path)}
        )
    
    # Build ctags command for standard format
    cmd = [
        ctags_path,
        '-f', '-',  # Output to stdout
        '--fields=+KSn',  # Include kind, scope, line number
        '--extras=+q',
        '--recurse=yes' if abs_path.is_dir() else '--recurse=no',
    ]
    
    # Add file patterns if extensions provided
    if extensions:
        for ext in extensions:
            cmd.extend([f'--include=*{ext}'])
    
    cmd.append(str(abs_path))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return create_error(
                "CTAGS_EXECUTION_ERROR",
                f"ctags failed with return code {result.returncode}",
                {
                    "stderr": result.stderr,
                    "command": ' '.join(cmd)
                }
            )
            
        return result.stdout
        
    except FileNotFoundError:
        return create_error(
            "CTAGS_NOT_FOUND",
            "ctags executable not found. Please install Universal Ctags.",
            {"ctags_path": ctags_path}
        )
    except Exception as e:
        return create_error(
            "CTAGS_UNKNOWN_ERROR",
            f"Unexpected error running ctags: {str(e)}",
            {"command": ' '.join(cmd)}
        )


def map_extension_to_language(extension: str) -> Optional[str]:
    """Map file extension to ctags language name."""
    mapping = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C,C++',
        '.hpp': 'C++',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'ObjectiveC',
        '.mm': 'ObjectiveC++',
        '.lua': 'Lua',
        '.perl': 'Perl',
        '.pl': 'Perl',
        '.sh': 'Sh',
        '.bash': 'Sh',
        '.zsh': 'Zsh',
        '.vim': 'Vim',
        '.el': 'EmacsLisp',
        '.clj': 'Clojure',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hrl': 'Erlang',
        '.ml': 'OCaml',
        '.mli': 'OCaml',
        '.fs': 'FSharp',
        '.fsi': 'FSharp',
        '.fsx': 'FSharp',
        '.hs': 'Haskell',
        '.lhs': 'Haskell',
        '.dart': 'Dart',
        '.groovy': 'Groovy',
        '.jl': 'Julia',
        '.nim': 'Nim',
        '.pas': 'Pascal',
        '.pp': 'Pascal',
        '.d': 'D',
        '.zig': 'Zig',
        '.v': 'Verilog',
        '.sv': 'SystemVerilog',
        '.vhd': 'VHDL',
        '.vhdl': 'VHDL',
        '.tcl': 'Tcl',
        '.awk': 'Awk',
        '.gawk': 'Awk',
        '.mawk': 'Awk',
        '.nawk': 'Awk',
        '.f': 'Fortran',
        '.for': 'Fortran',
        '.f90': 'Fortran',
        '.f95': 'Fortran',
        '.f03': 'Fortran',
        '.f08': 'Fortran',
        '.cob': 'Cobol',
        '.cbl': 'Cobol',
        '.ada': 'Ada',
        '.adb': 'Ada',
        '.ads': 'Ada',
        '.sql': 'SQL',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'Iniconf',
        '.cfg': 'Iniconf',
        '.properties': 'JavaProperties',
        '.mk': 'Make',
        '.makefile': 'Make',
        '.dockerfile': 'Dockerfile',
        '.tex': 'Tex',
        '.bib': 'BibTeX',
        '.rst': 'ReStructuredText',
        '.md': 'Markdown',
        '.adoc': 'Asciidoc',
        '.org': 'Org',
        '.pod': 'Pod',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.xhtml': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LessCSS',
    }
    
    return mapping.get(extension.lower())