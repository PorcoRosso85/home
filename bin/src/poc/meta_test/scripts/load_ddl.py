#!/usr/bin/env python3
"""Load DDL files into KuzuDB for meta_test system."""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure import load_ddl_directory, load_ddl_file
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main function to load DDL files."""
    parser = argparse.ArgumentParser(description="Load DDL files into KuzuDB")
    parser.add_argument(
        "path",
        type=str,
        help="Path to DDL file or directory"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=":memory:",
        help="Database path (default: :memory:)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.cypher",
        help="File pattern for directory loading (default: *.cypher)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["TRACE", "DEBUG", "INFO", "WARN", "ERROR"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--log-format",
        type=str,
        default="console",
        choices=["console", "json"],
        help="Log format (default: console)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    os.environ["META_TEST_LOG_LEVEL"] = args.log_level
    os.environ["LOG_FORMAT"] = args.log_format
    
    path = Path(args.path)
    
    # Create database connection
    logger.info(f"Connecting to database: {args.db_path}")
    
    try:
        with GraphAdapter(args.db_path) as graph:
            if path.is_file():
                # Load single file
                logger.info(f"Loading DDL file: {path}")
                result = load_ddl_file(graph, path)
                
                if isinstance(result, dict) and "statement_results" in result:
                    successful = sum(1 for r in result["statement_results"] if r["success"])
                    failed = sum(1 for r in result["statement_results"] if not r["success"])
                    
                    logger.info(
                        f"DDL loading completed",
                        total_statements=result["total_statements"],
                        successful=successful,
                        failed=failed
                    )
                    
                    # Show errors if any
                    if failed > 0:
                        for stmt_result in result["statement_results"]:
                            if not stmt_result["success"]:
                                logger.error(
                                    f"Failed statement: {stmt_result['error']}",
                                    statement_preview=stmt_result["statement"][:100]
                                )
                    
                    # Exit with error if any statements failed
                    if failed > 0:
                        sys.exit(1)
                else:
                    logger.error(f"Failed to load DDL file: {result}")
                    sys.exit(1)
                    
            elif path.is_dir():
                # Load directory
                logger.info(f"Loading DDL files from directory: {path}")
                logger.info(f"Using pattern: {args.pattern}")
                
                results = load_ddl_directory(graph, path, args.pattern)
                
                logger.info(
                    f"Directory loading completed",
                    files_processed=results["files_processed"],
                    total_statements=results["total_statements"],
                    successful_statements=results["successful_statements"],
                    failed_statements=results["failed_statements"]
                )
                
                # Show file-level summary
                if results["file_results"]:
                    logger.info("File summary:")
                    for file_result in results["file_results"]:
                        if "error" in file_result:
                            logger.error(f"  - {Path(file_result['file']).name}: ERROR - {file_result['error']['message']}")
                        else:
                            result = file_result["result"]
                            successful = sum(1 for r in result["statement_results"] if r["success"])
                            total = result["total_statements"]
                            logger.info(f"  - {Path(file_result['file']).name}: {successful}/{total} statements")
                
                # Show errors if any
                if results["errors"]:
                    logger.error("Errors encountered:")
                    for error in results["errors"]:
                        logger.error(f"  - {error}")
                
                # Exit with error if any statements failed
                if results["failed_statements"] > 0:
                    sys.exit(1)
                    
            else:
                logger.error(f"Path does not exist: {path}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Failed to load DDL: {e}")
        sys.exit(1)
        
    logger.info("DDL loading completed successfully")


if __name__ == "__main__":
    main()