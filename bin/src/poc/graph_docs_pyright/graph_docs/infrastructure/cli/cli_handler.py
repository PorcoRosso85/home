"""CLI handler - Infrastructure layer for command-line interface.

This module handles CLI arguments, command execution, and result display
using the application services.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

from graph_docs.application.analyzer_service import (
    AnalyzerService,
    AnalysisRequest,
    AnalysisResult,
    DualDBAnalysisResult
)
from graph_docs.application.interfaces.repository import IDualKuzuRepository
from graph_docs.infrastructure.kuzu.dual_kuzu_repository import DualKuzuRepository
import graph_docs.cli_display as cli_display


class CLIHandler:
    """Handles command-line interface operations."""
    
    def __init__(self, repository: Optional[IDualKuzuRepository] = None):
        """Initialize the CLI handler.
        
        Args:
            repository: Optional repository instance, creates default if not provided
        """
        self.repository = repository or DualKuzuRepository()
        self.analyzer_service = AnalyzerService(self.repository)
    
    def handle_query_command(self, args: argparse.Namespace) -> None:
        """Handle the query command.
        
        Args:
            args: Parsed command-line arguments
        """
        request = AnalysisRequest(
            db1_path=str(args.db1_path),
            db2_path=str(args.db2_path),
            query=args.query_text,
            target_db=args.single
        )
        
        result = self.analyzer_service.analyze(request)
        
        if args.json:
            self._output_json_result(result)
        else:
            self._display_analysis_result(result)
        
        if not result.ok:
            sys.exit(1)
    
    def handle_parallel_command(self, args: argparse.Namespace) -> None:
        """Handle the parallel query command.
        
        Args:
            args: Parsed command-line arguments
        """
        request = AnalysisRequest(
            db1_path=str(args.db1_path),
            db2_path=str(args.db2_path),
            db1_query=args.db1_query,
            db2_query=args.db2_query
        )
        
        result = self.analyzer_service.analyze_parallel(request)
        
        if args.json:
            self._output_json_parallel_result(result, args.db1_query, args.db2_query)
        else:
            cli_display.dual_query_info(args.db1_query, args.db2_query)
            self._display_analysis_result(result)
        
        if not result.ok:
            sys.exit(1)
    
    def handle_info_command(self, args: argparse.Namespace) -> None:
        """Handle the info command.
        
        Args:
            args: Parsed command-line arguments
        """
        db_info = self.analyzer_service.get_database_info(
            str(args.db1_path),
            str(args.db2_path)
        )
        
        if not db_info["ok"]:
            cli_display.error(f"Error: {db_info['error']}")
            sys.exit(1)
        
        # Display database paths
        cli_display.database_info(db_info["db1_path"], db_info["db2_path"])
        
        # Display DB1 tables
        cli_display.section_title("DB1 Tables")
        self._display_query_result(db_info["db1_tables"])
        
        # Display DB2 tables
        cli_display.section_title("DB2 Tables")
        self._display_query_result(db_info["db2_tables"])
    
    def handle_analyze_command(self, args: argparse.Namespace) -> None:
        """Handle the analyze command with optional Pyright integration.
        
        Args:
            args: Parsed command-line arguments
        """
        request = AnalysisRequest(
            db1_path=str(args.db1_path),
            db2_path=str(args.db2_path),
            query=args.query if hasattr(args, 'query') else None,
            target_db=args.single if hasattr(args, 'single') else None,
            enable_pyright=args.pyright,
            workspace_path=str(args.workspace) if args.pyright and args.workspace else None
        )
        
        if request.enable_pyright:
            result = self.analyzer_service.analyze_with_pyright(request)
            self._display_dual_analysis_result(result, args.json)
        else:
            result = self.analyzer_service.analyze(request)
            if args.json:
                self._output_json_result(result)
            else:
                self._display_analysis_result(result)
        
        if not result.ok:
            sys.exit(1)
    
    def handle_init_local_command(self, args: argparse.Namespace) -> None:
        """Handle the init-local command.
        
        Args:
            args: Parsed command-line arguments
        """
        result = self.analyzer_service.create_local_database(str(args.local_path))
        
        if result["ok"]:
            cli_display.info(result["message"])
        else:
            cli_display.error(f"Error: {result['error']}")
            if "details" in result:
                cli_display.error(f"Details: {result['details']}")
            sys.exit(1)
    
    def handle_create_relation_command(self, args: argparse.Namespace) -> None:
        """Handle the create-relation command.
        
        Args:
            args: Parsed command-line arguments
        """
        # Parse relation from JSON file if provided
        if hasattr(args, 'relation_file') and args.relation_file:
            try:
                with open(args.relation_file, 'r') as f:
                    relations = json.load(f)
                    if not isinstance(relations, list):
                        relations = [relations]
            except Exception as e:
                cli_display.error(f"Error reading relation file: {str(e)}")
                sys.exit(1)
        else:
            # Create single relation from command-line arguments
            relations = [{
                "from_id": args.from_id,
                "from_type": args.from_type,
                "to_id": args.to_id,
                "to_type": args.to_type,
                "rel_type": args.rel_type
            }]
        
        result = self.analyzer_service.create_relations(relations)
        
        if result["ok"]:
            cli_display.info("Relations created successfully")
            self._display_query_result(result["result"])
        else:
            cli_display.error(f"Error: {result['error']}")
            if "result" in result:
                self._display_query_result(result["result"])
            sys.exit(1)
    
    def handle_import_csv_command(self, args: argparse.Namespace) -> None:
        """Handle the import-csv command.
        
        Args:
            args: Parsed command-line arguments
        """
        result = self.analyzer_service.import_csv_data(
            args.target,
            args.table_name,
            str(args.csv_path)
        )
        
        if result["ok"]:
            cli_display.info("CSV import successful")
            self._display_query_result(result["result"])
        else:
            cli_display.error(f"Error: {result['error']}")
            if "result" in result:
                self._display_query_result(result["result"])
            sys.exit(1)
    
    def _display_query_result(self, result) -> None:
        """Display a single query result.
        
        Args:
            result: QueryResult object
        """
        cli_display.query_result(
            source=result.source,
            columns=result.columns,
            rows=result.rows,
            error=result.error
        )
    
    def _display_analysis_result(self, result: AnalysisResult) -> None:
        """Display an analysis result.
        
        Args:
            result: AnalysisResult object
        """
        if result.error and not (result.single_result or result.dual_result):
            cli_display.error(f"Error: {result.error}")
            return
        
        if result.single_result:
            self._display_query_result(result.single_result)
        elif result.dual_result:
            if result.dual_result.db1_result:
                self._display_query_result(result.dual_result.db1_result)
            
            cli_display.newline()
            
            if result.dual_result.db2_result:
                self._display_query_result(result.dual_result.db2_result)
            
            if result.dual_result.combined:
                cli_display.combined_results(result.dual_result.combined)
    
    def _display_dual_analysis_result(self, result: DualDBAnalysisResult, as_json: bool) -> None:
        """Display a dual analysis result (DB + Pyright).
        
        Args:
            result: DualDBAnalysisResult object
            as_json: Whether to output as JSON
        """
        if as_json:
            output = {
                "ok": result.ok,
                "error": result.error,
                "query_result": self._serialize_analysis_result(result.query_result),
                "pyright_result": result.pyright_result
            }
            cli_display.json_output(output)
        else:
            # Display query results
            self._display_analysis_result(result.query_result)
            
            # Display Pyright results if available
            if result.pyright_result:
                cli_display.section_title("Pyright Analysis")
                if result.pyright_result.get("ok"):
                    summary = result.pyright_result.get("summary", {})
                    cli_display.info(f"Errors: {summary.get('errors', 0)}")
                    cli_display.info(f"Warnings: {summary.get('warnings', 0)}")
                    cli_display.info(f"Information: {summary.get('information', 0)}")
                else:
                    cli_display.error(f"Pyright error: {result.pyright_result.get('error', 'Unknown error')}")
    
    def _output_json_result(self, result: AnalysisResult) -> None:
        """Output analysis result as JSON.
        
        Args:
            result: AnalysisResult object
        """
        output = self._serialize_analysis_result(result)
        cli_display.json_output(output)
    
    def _output_json_parallel_result(self, result: AnalysisResult, db1_query: str, db2_query: str) -> None:
        """Output parallel query result as JSON.
        
        Args:
            result: AnalysisResult object
            db1_query: Query executed on DB1
            db2_query: Query executed on DB2
        """
        output = {
            "ok": result.ok,
            "error": result.error
        }
        
        if result.dual_result:
            output["db1"] = {
                "query": db1_query,
                "columns": result.dual_result.db1_result.columns if result.dual_result.db1_result else [],
                "rows": result.dual_result.db1_result.rows if result.dual_result.db1_result else [],
                "error": result.dual_result.db1_result.error if result.dual_result.db1_result else None
            }
            output["db2"] = {
                "query": db2_query,
                "columns": result.dual_result.db2_result.columns if result.dual_result.db2_result else [],
                "rows": result.dual_result.db2_result.rows if result.dual_result.db2_result else [],
                "error": result.dual_result.db2_result.error if result.dual_result.db2_result else None
            }
        
        cli_display.json_output(output)
    
    def _serialize_analysis_result(self, result: AnalysisResult) -> Dict[str, Any]:
        """Serialize AnalysisResult to dictionary.
        
        Args:
            result: AnalysisResult object
            
        Returns:
            Serialized dictionary
        """
        output = {
            "ok": result.ok,
            "error": result.error
        }
        
        if result.single_result:
            output["result"] = {
                "source": result.single_result.source,
                "columns": result.single_result.columns,
                "rows": result.single_result.rows,
                "error": result.single_result.error
            }
        elif result.dual_result:
            output["db1"] = None
            output["db2"] = None
            
            if result.dual_result.db1_result:
                output["db1"] = {
                    "columns": result.dual_result.db1_result.columns,
                    "rows": result.dual_result.db1_result.rows,
                    "error": result.dual_result.db1_result.error
                }
            
            if result.dual_result.db2_result:
                output["db2"] = {
                    "columns": result.dual_result.db2_result.columns,
                    "rows": result.dual_result.db2_result.rows,
                    "error": result.dual_result.db2_result.error
                }
            
            if result.dual_result.combined:
                output["combined"] = result.dual_result.combined
        
        return output


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Graph-Docs: Dual KuzuDB Query Interface with Code Analysis"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Execute a query on one or both databases')
    query_parser.add_argument('db1_path', type=Path, help='Path to first KuzuDB database')
    query_parser.add_argument('db2_path', type=Path, help='Path to second KuzuDB database')
    query_parser.add_argument('query_text', help='Cypher query to execute')
    query_parser.add_argument('-s', '--single', choices=['db1', 'db2'],
                            help='Query only a single database')
    query_parser.add_argument('-j', '--json', action='store_true',
                            help='Output results as JSON')
    
    # Parallel command
    parallel_parser = subparsers.add_parser('parallel', 
                                          help='Execute different queries on each database')
    parallel_parser.add_argument('db1_path', type=Path, help='Path to first KuzuDB database')
    parallel_parser.add_argument('db2_path', type=Path, help='Path to second KuzuDB database')
    parallel_parser.add_argument('db1_query', help='Query for first database')
    parallel_parser.add_argument('db2_query', help='Query for second database')
    parallel_parser.add_argument('-j', '--json', action='store_true',
                               help='Output results as JSON')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Display database information')
    info_parser.add_argument('db1_path', type=Path, help='Path to first KuzuDB database')
    info_parser.add_argument('db2_path', type=Path, help='Path to second KuzuDB database')
    
    # Analyze command (with optional Pyright)
    analyze_parser = subparsers.add_parser('analyze', 
                                         help='Analyze databases with optional code analysis')
    analyze_parser.add_argument('db1_path', type=Path, help='Path to first KuzuDB database')
    analyze_parser.add_argument('db2_path', type=Path, help='Path to second KuzuDB database')
    analyze_parser.add_argument('-q', '--query', help='Optional query to execute')
    analyze_parser.add_argument('-s', '--single', choices=['db1', 'db2'],
                              help='Query only a single database')
    analyze_parser.add_argument('-p', '--pyright', action='store_true',
                              help='Enable Pyright code analysis')
    analyze_parser.add_argument('-w', '--workspace', type=Path,
                              help='Workspace path for Pyright analysis')
    analyze_parser.add_argument('-j', '--json', action='store_true',
                              help='Output results as JSON')
    
    # Init-local command
    init_parser = subparsers.add_parser('init-local', 
                                       help='Initialize a local database with schema')
    init_parser.add_argument('local_path', type=Path, help='Path for local database')
    
    # Create-relation command
    relation_parser = subparsers.add_parser('create-relation',
                                          help='Create relations in local database')
    relation_parser.add_argument('--from-id', help='Source node ID')
    relation_parser.add_argument('--from-type', help='Source node type')
    relation_parser.add_argument('--to-id', help='Target node ID')
    relation_parser.add_argument('--to-type', help='Target node type')
    relation_parser.add_argument('--rel-type', default='OWNS', help='Relation type (default: OWNS)')
    relation_parser.add_argument('-f', '--relation-file', type=Path,
                               help='JSON file containing relation definitions')
    
    # Import-csv command
    import_parser = subparsers.add_parser('import-csv',
                                        help='Import CSV data into a database table')
    import_parser.add_argument('target', choices=['db1', 'db2', 'local'],
                             help='Target database')
    import_parser.add_argument('table_name', help='Table name to import into')
    import_parser.add_argument('csv_path', type=Path, help='Path to CSV file')
    
    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Create CLI handler
    handler = CLIHandler()
    
    # Route to appropriate handler method
    command_handlers = {
        'query': handler.handle_query_command,
        'parallel': handler.handle_parallel_command,
        'info': handler.handle_info_command,
        'analyze': handler.handle_analyze_command,
        'init-local': handler.handle_init_local_command,
        'create-relation': handler.handle_create_relation_command,
        'import-csv': handler.handle_import_csv_command,
    }
    
    try:
        command_handler = command_handlers.get(args.command)
        if command_handler:
            command_handler(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        cli_display.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()