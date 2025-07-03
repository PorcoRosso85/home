#!/usr/bin/env python3
"""
Directory Scanner CLI Interface

規約遵守:
- 関数ベース設計
- エラーを値として扱う
"""

import sys
import argparse
from typing import Dict, Any

from infrastructure.variables.env import (
    get_scan_root_path, get_db_path, validate_environment,
    should_use_inmemory, should_skip_hidden, _optional_env
)
from main import create_directory_scanner


def create_cli_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        description="Directory Scanner with Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DIRSCAN_ROOT_PATH     Root directory to scan (required)
  DIRSCAN_DB_PATH       Database path (required)
  DIRSCAN_INMEMORY      Use in-memory mode (optional)
  DIRSCAN_SKIP_HIDDEN   Skip hidden directories (optional, default: true)

Commands:
  scan      Perform full directory scan
  update    Incremental update based on changes
  search    Search directories
  status    Show database status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Perform full directory scan')
    scan_parser.add_argument('--skip-empty', action='store_true', 
                           help='Skip empty directories')
    scan_parser.add_argument('--include-hidden', action='store_true',
                           help='Include hidden directories')
    scan_parser.add_argument('--with-embeddings', action='store_true',
                           help='Generate vector embeddings')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Incremental update')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search directories')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--type', choices=['fts', 'vss', 'hybrid'],
                             help='Search type (default: hybrid)')
    search_parser.add_argument('--limit', type=int,
                             help='Maximum results (default: 10)')
    search_parser.add_argument('--alpha', type=float,
                             help='Hybrid search weight (0=VSS, 1=FTS) (default: 0.5)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Show changes since last scan')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Build search indices')
    index_parser.add_argument('--type', choices=['fts', 'vss', 'all'],
                            default='all', help='Index type to build')
    
    return parser


def handle_scan(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle scan command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    print("Starting directory scan...")
    
    skip_hidden = not args.include_hidden if hasattr(args, 'include_hidden') else should_skip_hidden(_optional_env('DIRSCAN_SKIP_HIDDEN'), True)
    result = scanner['full_scan'](
        args.skip_empty,
        skip_hidden,
        args.with_embeddings
    )
    
    if result['ok']:
        print(f"\nScan completed successfully:")
        print(f"  Scanned: {result['scanned_count']} directories")
        print(f"  New: {result['new_count']}")
        print(f"  Duration: {result['duration_ms']:.0f}ms")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_update(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle update command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    print("Detecting changes...")
    
    # First show diff
    diff_result = scanner['detect_changes']()
    if not diff_result['ok']:
        print(f"Error: {diff_result['error']}", file=sys.stderr)
        return 1
    
    print(f"\nChanges detected:")
    print(f"  Added: {len(diff_result['added'])}")
    print(f"  Modified: {len(diff_result['modified'])}")
    print(f"  Deleted: {len(diff_result['deleted'])}")
    
    # Perform update
    print("\nApplying changes...")
    result = scanner['incremental_update']()
    
    if result['ok']:
        print(f"Update completed in {result['duration_ms']:.0f}ms")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_search(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle search command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    # デフォルト値を設定
    search_type = args.type or 'hybrid'
    limit = args.limit if args.limit is not None else 10
    alpha = args.alpha if args.alpha is not None else 0.5
    
    # Build indices if needed
    if search_type in ['fts', 'hybrid']:
        scanner['build_fts_index']()
    
    # Perform search
    if search_type == 'fts':
        result = scanner['search_fts'](args.query)
    elif search_type == 'vss':
        result = scanner['search_vss'](args.query, limit)
    else:  # hybrid
        result = scanner['search_hybrid'](args.query, alpha)
    
    if not result['ok']:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    
    # Display results
    print(f"\nSearch results for: '{args.query}'")
    print(f"Found {result['total']} matches (showing top {min(limit, len(result['hits']))})")
    print("-" * 60)
    
    for i, hit in enumerate(result['hits'][:limit], 1):
        print(f"\n{i}. {hit['path']} (score: {hit['score']:.3f})")
        if hit['snippet']:
            snippet = hit['snippet'].replace('\n', ' ')
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            print(f"   {snippet}")
    
    return 0


def handle_status(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle status command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    status = scanner['get_status']()
    
    print("Database Status")
    print("-" * 40)
    print(f"Total directories: {status['total_directories']}")
    print(f"Indexed (with embeddings): {status['indexed_directories']}")
    print(f"Database size: {status['db_size_mb']:.2f} MB")
    if status['last_scan']:
        print(f"Last scan: {status['last_scan']}")
    
    return 0


def handle_diff(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle diff command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    result = scanner['detect_changes']()
    
    if not result['ok']:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    
    print("Changes since last scan:")
    print("-" * 40)
    
    if result['added']:
        print(f"\nAdded ({len(result['added'])}):")
        for path in result['added'][:10]:
            print(f"  + {path}")
        if len(result['added']) > 10:
            print(f"  ... and {len(result['added']) - 10} more")
    
    if result['modified']:
        print(f"\nModified ({len(result['modified'])}):")
        for path in result['modified'][:10]:
            print(f"  ~ {path}")
        if len(result['modified']) > 10:
            print(f"  ... and {len(result['modified']) - 10} more")
    
    if result['deleted']:
        print(f"\nDeleted ({len(result['deleted'])}):")
        for path in result['deleted'][:10]:
            print(f"  - {path}")
        if len(result['deleted']) > 10:
            print(f"  ... and {len(result['deleted']) - 10} more")
    
    if not any([result['added'], result['modified'], result['deleted']]):
        print("No changes detected.")
    
    return 0


def handle_index(args: argparse.Namespace, scanner: Dict[str, Any]) -> int:
    """Handle index command
    
    Args:
        args: コマンドライン引数
        scanner: スキャナー操作辞書
        
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    if args.type in ['fts', 'all']:
        print("Building FTS index...")
        result = scanner['build_fts_index']()
        if result['ok']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ FTS index failed: {result['error']}")
            return 1
    
    if args.type in ['vss', 'all']:
        print("Building VSS index...")
        # VSS index is built during scan with generate_embeddings=True
        print("✓ Run 'scan --with-embeddings' to generate vector embeddings")
    
    return 0


def main() -> int:
    """Main CLI entry point
    
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    # Validate environment
    errors = validate_environment()
    if errors:
        print("Environment configuration errors:", file=sys.stderr)
        for var, error in errors.items():
            print(f"  {var}: {error}", file=sys.stderr)
        return 1
    
    # Parse arguments
    parser = create_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize scanner
    try:
        root_path = get_scan_root_path()
        db_path = get_db_path()
        
        scanner = create_directory_scanner(root_path, db_path)
    except Exception as e:
        print(f"Failed to initialize scanner: {e}", file=sys.stderr)
        return 1
    
    # Handle commands
    if args.command == 'scan':
        return handle_scan(args, scanner)
    elif args.command == 'update':
        return handle_update(args, scanner)
    elif args.command == 'search':
        return handle_search(args, scanner)
    elif args.command == 'status':
        return handle_status(args, scanner)
    elif args.command == 'diff':
        return handle_diff(args, scanner)
    elif args.command == 'index':
        return handle_index(args, scanner)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    # CLI should be run via 'uv run dirscan' or 'uv run python cli.py'
    # in nix develop environment
    sys.exit(main())