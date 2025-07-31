"""DDL loader utility for KuzuDB.

Provides functionality to load Cypher DDL files into KuzuDB,
handling file reading, statement parsing, and execution.
"""

import re
from pathlib import Path
from typing import Any

from .errors import DatabaseError, FileOperationError, ValidationError
from .graph_adapter import GraphAdapter
from .logger import get_logger

logger = get_logger(__name__)


class DDLLoader:
    """Loads DDL files into KuzuDB."""

    def __init__(self, graph_adapter: GraphAdapter):
        """Initialize DDL loader with graph adapter.
        
        Args:
            graph_adapter: GraphAdapter instance for database operations
        """
        self.graph_adapter = graph_adapter
        logger.debug("Initialized DDL loader")

    def load_file(self, file_path: str | Path) -> dict[str, Any] | FileOperationError | DatabaseError:
        """Load a DDL file into the database.
        
        Args:
            file_path: Path to the .cypher DDL file
            
        Returns:
            Dict with loading results or error
        """
        file_path = Path(file_path)
        
        # Validate file
        validation_result = self._validate_file(file_path)
        if isinstance(validation_result, dict) and validation_result.get("type") in ["FileOperationError", "ValidationError"]:
            return validation_result
            
        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
            logger.info(f"Read DDL file: {file_path}", file_size=len(content))
        except PermissionError:
            error: FileOperationError = {
                "type": "FileOperationError",
                "message": f"Permission denied reading file: {file_path}",
                "operation": "read",
                "file_path": str(file_path),
                "permission_issue": True,
                "exists": True
            }
            logger.error(error["message"], file_path=str(file_path))
            return error
        except Exception as e:
            error: FileOperationError = {
                "type": "FileOperationError",
                "message": f"Failed to read file: {str(e)}",
                "operation": "read",
                "file_path": str(file_path),
                "permission_issue": False,
                "exists": file_path.exists()
            }
            logger.error(error["message"], file_path=str(file_path), exception=str(e))
            return error
            
        # Parse and execute statements
        statements = self._parse_statements(content)
        logger.debug(f"Parsed {len(statements)} statements from {file_path}")
        
        results = self._execute_statements(statements, file_path)
        
        # Log summary
        success_count = sum(1 for r in results["statement_results"] if r["success"])
        logger.info(
            f"DDL loading completed for {file_path}",
            total_statements=results["total_statements"],
            successful=success_count,
            failed=results["total_statements"] - success_count
        )
        
        return results

    def load_directory(self, directory_path: str | Path, pattern: str = "*.cypher") -> dict[str, Any]:
        """Load all DDL files from a directory.
        
        Args:
            directory_path: Path to directory containing DDL files
            pattern: Glob pattern for DDL files (default: "*.cypher")
            
        Returns:
            Dict with loading results for all files
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return {
                "directory": str(directory_path),
                "pattern": pattern,
                "files_processed": 0,
                "total_statements": 0,
                "successful_statements": 0,
                "failed_statements": 0,
                "errors": [f"Directory does not exist: {directory_path}"]
            }
            
        if not directory_path.is_dir():
            logger.error(f"Path is not a directory: {directory_path}")
            return {
                "directory": str(directory_path),
                "pattern": pattern,
                "files_processed": 0,
                "total_statements": 0,
                "successful_statements": 0,
                "failed_statements": 0,
                "errors": [f"Path is not a directory: {directory_path}"]
            }
            
        # Find all matching files
        files = sorted(directory_path.glob(pattern))
        logger.info(f"Found {len(files)} DDL files in {directory_path}", pattern=pattern)
        
        # Process each file
        all_results = {
            "directory": str(directory_path),
            "pattern": pattern,
            "files_processed": 0,
            "total_statements": 0,
            "successful_statements": 0,
            "failed_statements": 0,
            "file_results": [],
            "errors": []
        }
        
        for file_path in files:
            logger.debug(f"Loading DDL file: {file_path}")
            result = self.load_file(file_path)
            
            if isinstance(result, dict) and result.get("type") in ["FileOperationError", "DatabaseError"]:
                all_results["errors"].append(f"{file_path}: {result['message']}")
                all_results["file_results"].append({
                    "file": str(file_path),
                    "error": result
                })
            else:
                all_results["files_processed"] += 1
                all_results["total_statements"] += result["total_statements"]
                all_results["successful_statements"] += sum(
                    1 for r in result["statement_results"] if r["success"]
                )
                all_results["failed_statements"] += sum(
                    1 for r in result["statement_results"] if not r["success"]
                )
                all_results["file_results"].append({
                    "file": str(file_path),
                    "result": result
                })
                
        logger.info(
            "Directory DDL loading completed",
            directory=str(directory_path),
            files_processed=all_results["files_processed"],
            total_statements=all_results["total_statements"],
            successful=all_results["successful_statements"],
            failed=all_results["failed_statements"]
        )
        
        return all_results

    def _validate_file(self, file_path: Path) -> dict[str, Any] | FileOperationError | ValidationError:
        """Validate DDL file before loading.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Dict with validation results or error
        """
        if not file_path.exists():
            error: FileOperationError = {
                "type": "FileOperationError",
                "message": f"File does not exist: {file_path}",
                "operation": "validate",
                "file_path": str(file_path),
                "permission_issue": False,
                "exists": False
            }
            logger.error(error["message"], file_path=str(file_path))
            return error
            
        if not file_path.is_file():
            error: ValidationError = {
                "type": "ValidationError",
                "message": f"Path is not a file: {file_path}",
                "field": "file_path",
                "value": str(file_path),
                "constraint": "must be a file",
                "suggestion": "Provide a path to a .cypher file, not a directory"
            }
            logger.error(error["message"], file_path=str(file_path))
            return error
            
        if file_path.suffix.lower() not in [".cypher", ".cql"]:
            error: ValidationError = {
                "type": "ValidationError",
                "message": f"Invalid file extension: {file_path.suffix}",
                "field": "file_extension",
                "value": file_path.suffix,
                "constraint": "must be .cypher or .cql",
                "suggestion": "Use .cypher extension for DDL files"
            }
            logger.warn(f"Non-standard file extension: {file_path.suffix}", file_path=str(file_path))
            # Don't return error, just warn - allow loading anyway
            
        return {"valid": True, "file_path": str(file_path)}

    def _parse_statements(self, content: str) -> list[str]:
        """Parse DDL content into individual statements.
        
        Handles:
        - Single-line and multi-line comments
        - Statements terminated by semicolons
        - Quoted strings containing semicolons
        - Empty statements
        
        Args:
            content: DDL file content
            
        Returns:
            List of individual DDL statements
        """
        # Remove single-line comments
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments (but not inside quotes)
            # Simple approach - doesn't handle all edge cases
            comment_pos = line.find('//')
            if comment_pos >= 0:
                # Check if it's inside quotes (simple check)
                before_comment = line[:comment_pos]
                if before_comment.count('"') % 2 == 0 and before_comment.count("'") % 2 == 0:
                    line = before_comment
            cleaned_lines.append(line)
            
        content = '\n'.join(cleaned_lines)
        
        # Remove multi-line comments /* ... */
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Split by semicolons, but not those inside quotes
        # This is a simplified approach - a full parser would be more robust
        statements = []
        current_statement = []
        in_single_quote = False
        in_double_quote = False
        
        for char in content:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == ';' and not in_single_quote and not in_double_quote:
                # End of statement
                statement = ''.join(current_statement).strip()
                if statement:  # Skip empty statements
                    statements.append(statement)
                current_statement = []
                continue
                
            current_statement.append(char)
            
        # Don't forget the last statement if it doesn't end with semicolon
        statement = ''.join(current_statement).strip()
        if statement:
            statements.append(statement)
            
        return statements

    def _execute_statements(self, statements: list[str], source_file: Path) -> dict[str, Any]:
        """Execute DDL statements.
        
        Args:
            statements: List of DDL statements to execute
            source_file: Source file for logging context
            
        Returns:
            Dict with execution results
        """
        results = {
            "source_file": str(source_file),
            "total_statements": len(statements),
            "statement_results": []
        }
        
        for i, statement in enumerate(statements):
            logger.debug(f"Executing statement {i+1}/{len(statements)}", 
                        statement_preview=statement[:100] + "..." if len(statement) > 100 else statement)
            
            try:
                # Use execute_cypher from GraphAdapter
                self.graph_adapter.execute_cypher(statement)
                
                results["statement_results"].append({
                    "index": i,
                    "statement": statement[:200] + "..." if len(statement) > 200 else statement,
                    "success": True,
                    "error": None
                })
                
                logger.trace(f"Statement {i+1} executed successfully")
                
            except Exception as e:
                error_msg = str(e)
                results["statement_results"].append({
                    "index": i,
                    "statement": statement[:200] + "..." if len(statement) > 200 else statement,
                    "success": False,
                    "error": error_msg
                })
                
                logger.error(
                    f"Failed to execute statement {i+1}",
                    statement_preview=statement[:100] + "..." if len(statement) > 100 else statement,
                    error=error_msg
                )
                
                # Check if it's a non-critical error (e.g., "already exists")
                if "already exists" in error_msg.lower():
                    logger.debug("Non-critical error - object already exists")
                elif "not exists" in error_msg.lower():
                    logger.debug("IF NOT EXISTS clause handled the error")
                else:
                    # For critical errors, we might want to stop
                    # But for now, continue with remaining statements
                    pass
                    
        return results


def load_ddl_file(graph_adapter: GraphAdapter, file_path: str | Path) -> dict[str, Any] | FileOperationError | DatabaseError:
    """Convenience function to load a single DDL file.
    
    Args:
        graph_adapter: GraphAdapter instance
        file_path: Path to DDL file
        
    Returns:
        Loading results or error
    """
    loader = DDLLoader(graph_adapter)
    return loader.load_file(file_path)


def load_ddl_directory(graph_adapter: GraphAdapter, directory_path: str | Path, pattern: str = "*.cypher") -> dict[str, Any]:
    """Convenience function to load all DDL files from a directory.
    
    Args:
        graph_adapter: GraphAdapter instance
        directory_path: Directory containing DDL files
        pattern: Glob pattern for files (default: "*.cypher")
        
    Returns:
        Loading results for all files
    """
    loader = DDLLoader(graph_adapter)
    return loader.load_directory(directory_path, pattern)