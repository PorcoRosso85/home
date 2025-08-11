"""Command-line interface for flake-graph."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from .architecture_analyzer import analyze_architecture
from .duplicate_detector import find_duplicate_flakes
from .readme_checker import generate_missing_readme_report
from .scanner import scan_flake_description, scan_readme_content
from .exporter import FlakeExporter
from .search_command import search_flakes, format_search_results
from .dependency_command import cmd_dependencies


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze flakes with optional architecture analysis."""
    # Prepare flake documents for VSS indexing
    flakes: List[Dict[str, str]] = []
    
    # Scan for flakes in the target directory
    target_path = Path(args.path)
    if not target_path.exists():
        sys.stderr.write(f"Error: Path {target_path} does not exist\n")
        return 1
    
    # Simple flake scanning (can be enhanced)
    for flake_path in target_path.rglob("flake.nix"):
        flake_dir = flake_path.parent
        description = scan_flake_description(flake_path)
        readme = scan_readme_content(flake_dir)
        
        if description or readme:
            flakes.append({
                "id": str(flake_dir.relative_to(target_path)),
                "content": f"{description or ''}\n{readme or ''}",
                "path": str(flake_dir)
            })
    
    if not flakes:
        sys.stderr.write("No flakes found in the specified directory\n")
        return 1
    
    if args.architecture:
        # Run architecture analysis
        result = analyze_architecture(
            flake_path=args.path,
            query=args.query or "architecture health",
            flakes=flakes,
            db_path=args.db_path,
            language=args.language
        )
        
        # Display results
        health = result["architecture_health"]
        sys.stdout.write(f"Architecture Health Score: {health['score']:.2f}\n")
        sys.stdout.write("\nMetrics:\n")
        metrics = health["metrics"]
        if metrics["vss_score"] is not None:
            sys.stdout.write(f"  VSS Score: {metrics['vss_score']:.2f}\n")
        if metrics["ast_score"] is not None:
            sys.stdout.write(f"  AST Score: {metrics['ast_score']:.2f}\n")
        sys.stdout.write(f"  Duplication Ratio: {metrics['duplication_ratio']:.2f}\n")
        sys.stdout.write(f"  Consistency Score: {metrics['consistency_score']:.2f}\n")
        sys.stdout.write(f"  Coupling Index: {metrics['coupling_index']:.2f}\n")
        
        if health["issues"]:
            sys.stdout.write(f"\nIssues Found ({len(health['issues'])}):\n")
            for issue in health["issues"]:
                sys.stdout.write(f"\n[{issue['severity'].upper()}] {issue['type']}\n")
                sys.stdout.write(f"  {issue['description']}\n")
                if issue["affected_files"]:
                    sys.stdout.write(f"  Affected files: {', '.join(issue['affected_files'])}\n")
        else:
            sys.stdout.write("\nNo issues found!\n")
        
        if args.json:
            sys.stdout.write("\nJSON Output:\n")
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        # Standard analyze (list flakes)
        sys.stdout.write(f"Found {len(flakes)} flakes:\n")
        for flake in flakes:
            sys.stdout.write(f"  - {flake['id']}\n")
            if args.verbose:
                content_preview = flake['content'][:100].replace('\n', ' ')
                if len(flake['content']) > 100:
                    content_preview += "..."
                sys.stdout.write(f"    Content: {content_preview}\n")
    
    return 0


def cmd_check_readme(args: argparse.Namespace) -> int:
    """Check for missing README files."""
    target_path = Path(args.path)
    if not target_path.exists():
        sys.stderr.write(f"Error: Path {target_path} does not exist\n")
        return 1
    
    report = generate_missing_readme_report(target_path)
    sys.stdout.write(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        sys.stdout.write(f"\nReport saved to: {output_path}\n")
    
    return 0


def cmd_detect_duplicates(args: argparse.Namespace) -> int:
    """Detect duplicate flakes."""
    target_path = Path(args.path)
    if not target_path.exists():
        sys.stderr.write(f"Error: Path {target_path} does not exist\n")
        return 1
    
    # Scan for flakes
    flakes = []
    for flake_path in target_path.rglob("flake.nix"):
        flake_dir = flake_path.parent
        description = scan_flake_description(flake_path)
        if description:
            flakes.append({
                "description": description,
                "path": flake_dir
            })
    
    if not flakes:
        sys.stderr.write("No flakes found in the specified directory\n")
        return 1
    
    # Find duplicates
    duplicates = find_duplicate_flakes(
        flakes,
        use_vss=args.use_vss,
        similarity_threshold=args.similarity_threshold
    )
    
    if duplicates:
        sys.stdout.write(f"Found {len(duplicates)} groups of duplicate flakes:\n")
        for i, group in enumerate(duplicates, 1):
            sys.stdout.write(f"\nGroup {i}:\n")
            sys.stdout.write(f"  Description: {group['description']}\n")
            if "similarity_score" in group:
                sys.stdout.write(f"  Similarity Score: {group['similarity_score']:.2f}\n")
            sys.stdout.write("  Flakes:\n")
            for flake in group["flakes"]:
                sys.stdout.write(f"    - {flake['path']}\n")
        
        if args.json:
            # Convert Path objects to strings for JSON serialization
            json_duplicates = []
            for group in duplicates:
                json_group = group.copy()
                json_group["flakes"] = [
                    {**f, "path": str(f["path"])} for f in group["flakes"]
                ]
                json_duplicates.append(json_group)
            sys.stdout.write("\nJSON Output:\n")
            sys.stdout.write(json.dumps(json_duplicates, indent=2) + "\n")
    else:
        sys.stdout.write("No duplicate flakes found.\n")
    
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export flake data from KuzuDB."""
    # Validate format (currently only JSON is supported)
    if args.format != "json":
        sys.stderr.write(f"Error: Format '{args.format}' is not supported yet. Only 'json' is available.\n")
        return 1
    
    # Initialize exporter with database path
    db_path = Path(args.db_path)
    if not db_path.exists():
        sys.stderr.write(f"Error: Database path {db_path} does not exist\n")
        return 1
    
    exporter = FlakeExporter(db_path)
    
    try:
        # Export to JSON with specified options
        result = exporter.export_to_json(
            output_path=args.output,
            language_filter=args.language,
            include_embeddings=args.include_embeddings,
            pretty_print=True
        )
        
        # Display results
        sys.stdout.write("Export successful!\n")
        sys.stdout.write(f"  Output file: {result['output_path']}\n")
        sys.stdout.write(f"  Total flakes exported: {result['total_exported']}\n")
        sys.stdout.write(f"  File size: {result['file_size_bytes']:,} bytes\n")
        
        if result['metadata']['language_filter']:
            sys.stdout.write(f"  Language filter: {result['metadata']['language_filter']}\n")
        
        sys.stdout.write(f"  Embeddings included: {result['metadata']['embeddings_included']}\n")
        
        if result['metadata']['languages']:
            sys.stdout.write("\nFlakes by language:\n")
            for lang, count in sorted(result['metadata']['languages'].items()):
                sys.stdout.write(f"    {lang}: {count}\n")
        
    except Exception as e:
        sys.stderr.write(f"Error during export: {e}\n")
        return 1
    finally:
        exporter.close()
    
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search for flakes by description and path."""
    target_path = Path(args.path)
    if not target_path.exists():
        sys.stderr.write(f"Error: Path {target_path} does not exist\n")
        return 1
    
    try:
        # Perform search
        results = search_flakes(
            query=args.query,
            search_path=str(target_path),
            use_vss=args.use_vss,
            db_path=args.db_path,
            limit=args.limit if hasattr(args, 'limit') else 10
        )
        
        # Format and output results
        output = format_search_results(results, output_json=args.json)
        sys.stdout.write(output)
        
        # Add newline if not JSON
        if not args.json:
            sys.stdout.write("\n")
        
        return 0
    except Exception as e:
        sys.stderr.write(f"Error during search: {e}\n")
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Flake responsibility graph explorer - makes flake responsibilities searchable"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze flakes (use --architecture for architecture health analysis)"
    )
    analyze_parser.add_argument(
        "path",
        help="Path to analyze"
    )
    analyze_parser.add_argument(
        "--architecture",
        action="store_true",
        help="Enable architecture health analysis"
    )
    analyze_parser.add_argument(
        "--query",
        help="Query string for VSS search (default: 'architecture health')"
    )
    analyze_parser.add_argument(
        "--db-path",
        default="vss.db",
        help="Path to VSS database (default: vss.db)"
    )
    analyze_parser.add_argument(
        "--language",
        default="python",
        choices=["python", "typescript", "rust"],
        help="Programming language for AST analysis (default: python)"
    )
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    analyze_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    # Check README command
    readme_parser = subparsers.add_parser(
        "check-readme",
        help="Check for missing README files"
    )
    readme_parser.add_argument(
        "path",
        help="Root directory to check"
    )
    readme_parser.add_argument(
        "--output",
        help="Save report to file"
    )
    
    # Detect duplicates command
    dup_parser = subparsers.add_parser(
        "detect-duplicates",
        help="Detect duplicate flakes"
    )
    dup_parser.add_argument(
        "path",
        help="Directory to scan"
    )
    dup_parser.add_argument(
        "--use-vss",
        action="store_true",
        help="Use VSS for similarity-based duplicate detection"
    )
    dup_parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.8,
        help="Minimum similarity score for VSS matching (default: 0.8)"
    )
    dup_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export flake data from KuzuDB"
    )
    export_parser.add_argument(
        "--db-path",
        default="vss.db",
        help="Path to KuzuDB database (default: vss.db)"
    )
    export_parser.add_argument(
        "--format",
        default="json",
        choices=["json"],
        help="Output format (default: json, future formats can be added)"
    )
    export_parser.add_argument(
        "--language",
        help="Filter by programming language (e.g., python, typescript, rust)"
    )
    export_parser.add_argument(
        "--include-embeddings",
        action="store_true",
        default=False,
        help="Include VSS embeddings in the export (default: False)"
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Output file path for the exported data"
    )
    
    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for flakes by description and path"
    )
    search_parser.add_argument(
        "query",
        help="Search query (keywords to search for)"
    )
    search_parser.add_argument(
        "--path",
        default=".",
        help="Path to search for flakes (default: current directory)"
    )
    search_parser.add_argument(
        "--use-vss",
        action="store_true",
        help="Use VSS for similarity-based search"
    )
    search_parser.add_argument(
        "--db-path",
        default="vss.db",
        help="Path to VSS database (default: vss.db)"
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)"
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    # Dependencies command
    deps_parser = subparsers.add_parser(
        "deps",
        help="Analyze flake dependencies"
    )
    deps_parser.add_argument(
        "flake_path",
        help="Path to the flake to analyze"
    )
    deps_parser.add_argument(
        "--path",
        default=".",
        help="Root path to search for flakes (default: current directory)"
    )
    deps_parser.add_argument(
        "--reverse",
        action="store_true",
        help="Show reverse dependencies (what depends on this flake)"
    )
    deps_parser.add_argument(
        "--tree",
        action="store_true",
        help="Display dependencies in tree format"
    )
    deps_parser.add_argument(
        "--depth",
        type=int,
        help="Maximum depth for tree traversal"
    )
    deps_parser.add_argument(
        "--check-cycles",
        action="store_true",
        help="Check for circular dependencies"
    )
    deps_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    # Architecture analyze shortcut (for backward compatibility)
    arch_parser = subparsers.add_parser(
        "architecture-analyze",
        help="Analyze architecture health (shortcut for 'analyze --architecture')"
    )
    arch_parser.add_argument(
        "path",
        help="Path to analyze"
    )
    arch_parser.add_argument(
        "--query",
        help="Query string for VSS search (default: 'architecture health')"
    )
    arch_parser.add_argument(
        "--db-path",
        default="vss.db",
        help="Path to VSS database (default: vss.db)"
    )
    arch_parser.add_argument(
        "--language",
        default="python",
        choices=["python", "typescript", "rust"],
        help="Programming language for AST analysis (default: python)"
    )
    arch_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "architecture-analyze":
        # Convert to analyze command with --architecture flag
        args.architecture = True
        args.verbose = False  # Add missing attribute
        return cmd_analyze(args)
    elif args.command == "check-readme":
        return cmd_check_readme(args)
    elif args.command == "detect-duplicates":
        return cmd_detect_duplicates(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "deps":
        return cmd_dependencies(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())