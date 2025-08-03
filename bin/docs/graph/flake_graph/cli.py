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


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze flakes with optional architecture analysis."""
    # Prepare flake documents for VSS indexing
    flakes: List[Dict[str, str]] = []
    
    # Scan for flakes in the target directory
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist", file=sys.stderr)
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
        print("No flakes found in the specified directory", file=sys.stderr)
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
        print(f"Architecture Health Score: {health['score']:.2f}")
        print(f"\nMetrics:")
        metrics = health["metrics"]
        if metrics["vss_score"] is not None:
            print(f"  VSS Score: {metrics['vss_score']:.2f}")
        if metrics["ast_score"] is not None:
            print(f"  AST Score: {metrics['ast_score']:.2f}")
        print(f"  Duplication Ratio: {metrics['duplication_ratio']:.2f}")
        print(f"  Consistency Score: {metrics['consistency_score']:.2f}")
        print(f"  Coupling Index: {metrics['coupling_index']:.2f}")
        
        if health["issues"]:
            print(f"\nIssues Found ({len(health['issues'])}):")
            for issue in health["issues"]:
                print(f"\n[{issue['severity'].upper()}] {issue['type']}")
                print(f"  {issue['description']}")
                if issue["affected_files"]:
                    print(f"  Affected files: {', '.join(issue['affected_files'])}")
        else:
            print("\nNo issues found!")
        
        if args.json:
            print("\nJSON Output:")
            print(json.dumps(result, indent=2))
    else:
        # Standard analyze (list flakes)
        print(f"Found {len(flakes)} flakes:")
        for flake in flakes:
            print(f"  - {flake['id']}")
            if args.verbose:
                content_preview = flake['content'][:100].replace('\n', ' ')
                if len(flake['content']) > 100:
                    content_preview += "..."
                print(f"    Content: {content_preview}")
    
    return 0


def cmd_check_readme(args: argparse.Namespace) -> int:
    """Check for missing README files."""
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist", file=sys.stderr)
        return 1
    
    report = generate_missing_readme_report(target_path)
    print(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"\nReport saved to: {output_path}")
    
    return 0


def cmd_detect_duplicates(args: argparse.Namespace) -> int:
    """Detect duplicate flakes."""
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist", file=sys.stderr)
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
        print("No flakes found in the specified directory", file=sys.stderr)
        return 1
    
    # Find duplicates
    duplicates = find_duplicate_flakes(
        flakes,
        use_vss=args.use_vss,
        similarity_threshold=args.similarity_threshold
    )
    
    if duplicates:
        print(f"Found {len(duplicates)} groups of duplicate flakes:")
        for i, group in enumerate(duplicates, 1):
            print(f"\nGroup {i}:")
            print(f"  Description: {group['description']}")
            if "similarity_score" in group:
                print(f"  Similarity Score: {group['similarity_score']:.2f}")
            print("  Flakes:")
            for flake in group["flakes"]:
                print(f"    - {flake['path']}")
        
        if args.json:
            # Convert Path objects to strings for JSON serialization
            json_duplicates = []
            for group in duplicates:
                json_group = group.copy()
                json_group["flakes"] = [
                    {**f, "path": str(f["path"])} for f in group["flakes"]
                ]
                json_duplicates.append(json_group)
            print("\nJSON Output:")
            print(json.dumps(json_duplicates, indent=2))
    else:
        print("No duplicate flakes found.")
    
    return 0


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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())