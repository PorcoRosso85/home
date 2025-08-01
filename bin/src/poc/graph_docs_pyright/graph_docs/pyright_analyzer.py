"""Simple Pyright-based analyzer using subprocess."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Union, TypedDict


class PyrightAnalysisResult(TypedDict):
    """Successful Pyright analysis result."""
    ok: bool
    diagnostics: List[Dict[str, Any]]
    summary: Dict[str, Any]
    files: List[Dict[str, Any]]


class PyrightAnalysisError(TypedDict):
    """Error result from Pyright analysis."""
    ok: bool
    error: str


class PyrightAnalyzer:
    """Analyze Python code using Pyright CLI directly."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        
    def analyze(self) -> Union[PyrightAnalysisResult, PyrightAnalysisError]:
        """Run Pyright analysis and return results."""
        # Run pyright with JSON output
        result = subprocess.run(
            ["pyright", "--outputjson"],
            cwd=self.workspace_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode not in [0, 1]:  # 0 = no errors, 1 = has errors
            return PyrightAnalysisError(
                ok=False,
                error=f"Pyright failed with return code {result.returncode}: {result.stderr}"
            )
            
        # Parse JSON output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return PyrightAnalysisError(
                ok=False,
                error=f"Failed to parse Pyright output: {str(e)}"
            )
        
        return PyrightAnalysisResult(
            ok=True,
            diagnostics=output.get("diagnostics", []),
            summary=output.get("summary", {}),
            files=self._extract_files_info(output)
        )
        
    def _extract_files_info(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract file information from diagnostics."""
        files = {}
        
        for diag in output.get("diagnostics", []):
            file_path = diag.get("file", "")
            if file_path not in files:
                files[file_path] = {
                    "path": file_path,
                    "errors": 0,
                    "warnings": 0,
                    "information": 0
                }
            
            severity = diag.get("severity", "error")
            if severity == "error":
                files[file_path]["errors"] += 1
            elif severity == "warning":
                files[file_path]["warnings"] += 1
            else:
                files[file_path]["information"] += 1
                
        return list(files.values())