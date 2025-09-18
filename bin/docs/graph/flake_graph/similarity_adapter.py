"""Code similarity detection adapter for flake exploration."""

import subprocess
from pathlib import Path
from typing import TypedDict, Union, List


class SimilarityMatch(TypedDict):
    """A code similarity match."""
    file1: str
    file2: str
    similarity: float
    details: str


class SimilarityResult(TypedDict):
    """Successful similarity detection result."""
    ok: bool
    matches: List[SimilarityMatch]
    total_files: int
    language: str


class SimilarityError(TypedDict):
    """Error result from similarity detection."""
    ok: bool
    error: str


def detect_code_similarity(
    flake_path: str,
    language: str = 'python'
) -> Union[SimilarityResult, SimilarityError]:
    """Detect code similarity within a flake project.
    
    Args:
        flake_path: Path to the flake directory
        language: Programming language (python, rust, go, etc.)
    
    Returns:
        Either SimilarityResult with matches or SimilarityError
    """
    # Verify path exists
    path = Path(flake_path)
    if not path.exists():
        return SimilarityError(
            ok=False,
            error=f"Path does not exist: {flake_path}"
        )
    
    if not path.is_dir():
        return SimilarityError(
            ok=False,
            error=f"Path is not a directory: {flake_path}"
        )
    
    # Construct command
    tool_name = f"similarity-{language}"
    cmd = [tool_name, str(path)]
    
    try:
        # Execute similarity detection tool
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if tool is not found
        if result.returncode == 127 or "command not found" in result.stderr:
            return SimilarityError(
                ok=False,
                error=f"Tool '{tool_name}' is not installed or not in PATH"
            )
        
        # Check for other errors
        if result.returncode != 0:
            return SimilarityError(
                ok=False,
                error=f"Tool execution failed: {result.stderr}"
            )
        
        # Parse output
        return _parse_similarity_output(result.stdout, language)
        
    except FileNotFoundError:
        return SimilarityError(
            ok=False,
            error=f"Tool '{tool_name}' is not installed or not in PATH"
        )
    except Exception as e:
        return SimilarityError(
            ok=False,
            error=f"Unexpected error: {str(e)}"
        )


def _parse_similarity_output(output: str, language: str) -> Union[SimilarityResult, SimilarityError]:
    """Parse similarity tool output into structured data.
    
    Expected format (example):
    file1.py <-> file2.py: 85.3% similar
    - Both files contain similar function structures
    - Shared imports: os, sys, pathlib
    
    file3.py <-> file4.py: 92.1% similar
    - Identical class definitions
    """
    try:
        lines = output.strip().split('\n')
        matches: List[SimilarityMatch] = []
        total_files = 0
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Parse similarity line
            if '<->' in line and '%' in line:
                parts = line.split('<->')
                if len(parts) == 2:
                    file1 = parts[0].strip()
                    remainder = parts[1].strip()
                    
                    # Extract percentage
                    colon_idx = remainder.find(':')
                    percent_idx = remainder.find('%')
                    
                    if colon_idx != -1 and percent_idx != -1:
                        file2 = remainder[:colon_idx].strip()
                        percent_str = remainder[colon_idx+1:percent_idx].strip()
                        
                        try:
                            similarity = float(percent_str)
                        except ValueError:
                            i += 1
                            continue
                        
                        # Collect details from following lines
                        details_lines = []
                        i += 1
                        while i < len(lines) and lines[i].startswith(('-', ' ')):
                            details_lines.append(lines[i].strip())
                            i += 1
                        
                        matches.append(SimilarityMatch(
                            file1=file1,
                            file2=file2,
                            similarity=similarity,
                            details='\n'.join(details_lines)
                        ))
                        
                        # Count unique files
                        if file1 not in [m['file1'] for m in matches[:-1]] + [m['file2'] for m in matches[:-1]]:
                            total_files += 1
                        if file2 not in [m['file1'] for m in matches] + [m['file2'] for m in matches[:-1]]:
                            total_files += 1
                        continue
            
            i += 1
        
        return SimilarityResult(
            ok=True,
            matches=matches,
            total_files=total_files,
            language=language
        )
        
    except Exception as e:
        return SimilarityError(
            ok=False,
            error=f"Failed to parse output: {str(e)}"
        )