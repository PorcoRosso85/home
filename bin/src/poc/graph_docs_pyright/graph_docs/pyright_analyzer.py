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
        
    def analyze(self, filter_external: bool = False) -> Union[PyrightAnalysisResult, PyrightAnalysisError]:
        """Run Pyright analysis and return results.
        
        Args:
            filter_external: If True, filter out diagnostics and files outside workspace_path
        """
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
        
        diagnostics = output.get("generalDiagnostics", output.get("diagnostics", []))
        
        # Filter diagnostics if requested
        if filter_external:
            diagnostics = self._filter_internal_diagnostics(diagnostics)
        
        return PyrightAnalysisResult(
            ok=True,
            diagnostics=diagnostics,
            summary=output.get("summary", {}),
            files=self._extract_files_info(output, filter_external)
        )
        
    def _filter_internal_diagnostics(self, diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter diagnostics to only include those within workspace_path."""
        filtered: List[Dict[str, Any]] = []
        workspace_abs = self.workspace_path.resolve()
        
        for diag in diagnostics:
            file_path = diag.get("file", "")
            if file_path:
                try:
                    diag_path = Path(file_path).resolve()
                    # Check if the diagnostic file is within the workspace
                    if workspace_abs in diag_path.parents or diag_path == workspace_abs:
                        filtered.append(diag)
                except (ValueError, OSError):
                    # Skip invalid paths
                    continue
            else:
                # Include diagnostics without file paths (general errors)
                filtered.append(diag)
                
        return filtered
    
    def _extract_files_info(self, output: Dict[str, Any], filter_external: bool = False) -> List[Dict[str, Any]]:
        """Extract file information from diagnostics."""
        files: Dict[str, Dict[str, Any]] = {}
        diagnostics = output.get("generalDiagnostics", output.get("diagnostics", []))
        workspace_abs = self.workspace_path.resolve() if filter_external else None
        
        for diag in diagnostics:
            file_path = diag.get("file", "")
            
            # Skip external files if filtering is enabled
            if filter_external and file_path:
                try:
                    diag_path = Path(file_path).resolve()
                    if workspace_abs not in diag_path.parents and diag_path != workspace_abs:
                        continue
                except (ValueError, OSError):
                    continue
            
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