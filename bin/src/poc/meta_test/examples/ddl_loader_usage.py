#!/usr/bin/env python3
"""Example usage of the DDL loader utility."""

import os
from pathlib import Path

from infrastructure import load_ddl_directory, load_ddl_file
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger

logger = get_logger(__name__)


def main():
    """Demonstrate DDL loader usage."""
    # Set up logging
    os.environ["META_TEST_LOG_LEVEL"] = "DEBUG"
    
    # Create in-memory database for demonstration
    logger.info("Creating in-memory database for DDL loading demo")
    
    with GraphAdapter(":memory:") as graph:
        # Example 1: Load a single DDL file
        logger.info("Example 1: Loading a single DDL file")
        schema_file = Path(__file__).parent.parent / "data" / "schema" / "meta_test_schema.cypher"
        
        if schema_file.exists():
            result = load_ddl_file(graph, schema_file)
            
            if isinstance(result, dict) and "statement_results" in result:
                logger.info(
                    f"Loaded {result['total_statements']} statements from {schema_file.name}",
                    successful=sum(1 for r in result["statement_results"] if r["success"]),
                    failed=sum(1 for r in result["statement_results"] if not r["success"])
                )
                
                # Show any errors
                for stmt_result in result["statement_results"]:
                    if not stmt_result["success"]:
                        logger.error(
                            f"Failed statement {stmt_result['index']}: {stmt_result['error']}",
                            statement=stmt_result["statement"][:100]
                        )
            else:
                logger.error(f"Failed to load DDL file: {result}")
        else:
            logger.warn(f"Schema file not found: {schema_file}")
            
        # Example 2: Load all DDL files from a directory
        logger.info("Example 2: Loading all DDL files from a directory")
        ddl_dir = Path(__file__).parent.parent / "ddl"
        
        if ddl_dir.exists():
            results = load_ddl_directory(graph, ddl_dir)
            
            logger.info(
                f"Directory loading completed",
                files_processed=results["files_processed"],
                total_statements=results["total_statements"],
                successful_statements=results["successful_statements"],
                failed_statements=results["failed_statements"]
            )
            
            # Show file-level summary
            for file_result in results["file_results"]:
                if "error" in file_result:
                    logger.error(f"File error: {file_result['file']} - {file_result['error']['message']}")
                else:
                    result = file_result["result"]
                    logger.info(
                        f"File: {Path(file_result['file']).name}",
                        statements=result["total_statements"],
                        successful=sum(1 for r in result["statement_results"] if r["success"])
                    )
        else:
            logger.warn(f"DDL directory not found: {ddl_dir}")
            
        # Example 3: Using DDLLoader class directly for more control
        logger.info("Example 3: Using DDLLoader class directly")
        from infrastructure.ddl_loader import DDLLoader
        
        loader = DDLLoader(graph)
        
        # Load with custom pattern
        migration_dir = Path(__file__).parent.parent / "ddl"
        if migration_dir.exists():
            results = loader.load_directory(migration_dir, pattern="migration_*.cypher")
            logger.info(
                f"Loaded migration files",
                pattern="migration_*.cypher",
                files_found=len(results["file_results"])
            )
            
        # Try to query loaded schema
        logger.info("Verifying loaded schema by querying tables")
        try:
            # This might fail if KuzuDB doesn't support these system queries
            # Just for demonstration
            result = graph.execute_cypher("CALL db.tables() RETURN name")
            logger.info(f"Tables created: {result}")
        except Exception as e:
            logger.debug(f"Could not query tables (expected): {e}")


if __name__ == "__main__":
    main()