#!/usr/bin/env python3
"""CLI entry point for org project - orchestrates Claude Code workers in tmux."""

import argparse
import sys
import os
from pathlib import Path

# Add current directory to path to import local modules
sys.path.insert(0, str(Path(__file__).parent))

from application import (
    start_worker_in_directory,
    send_command_to_worker_by_directory,
    get_all_workers_status,
    clean_dead_workers_from_state
)


def cmd_start_worker(args):
    """Handle start-worker command."""
    directory = os.path.abspath(args.directory)
    result = start_worker_in_directory(directory)
    
    if result["ok"]:
        data = result["data"]
        print(f"✓ Worker started in directory: {data['directory']}")
        print(f"  Window: {data['window_name']}")
        print(f"  Pane ID: {data['pane_id']}")
        return 0
    else:
        error = result["error"]
        print(f"✗ Failed to start worker: {error['message']}", file=sys.stderr)
        if args.verbose:
            print(f"  Error code: {error['code']}", file=sys.stderr)
        return 1


def cmd_send_command(args):
    """Handle send-command command."""
    directory = os.path.abspath(args.directory)
    result = send_command_to_worker_by_directory(directory, args.command)
    
    if result["ok"]:
        data = result["data"]
        print(f"✓ Command sent to worker in {data['directory']}")
        print(f"  Command: {data['command']}")
        print(f"  Pane ID: {data['pane_id']}")
        return 0
    else:
        error = result["error"]
        print(f"✗ Failed to send command: {error['message']}", file=sys.stderr)
        if args.verbose:
            print(f"  Error code: {error['code']}", file=sys.stderr)
        return 1


def cmd_status(args):
    """Handle status command."""
    result = get_all_workers_status()
    
    if result["ok"]:
        data = result["data"]
        workers = data["workers"]
        total = data["total"]
        
        if total == 0:
            print("No workers found.")
            return 0
        
        print(f"Found {total} worker{'s' if total != 1 else ''}:")
        for worker in workers:
            status_icon = "✓" if worker["status"] == "alive" else "✗"
            print(f"  {status_icon} {worker['directory']} ({worker['status']})")
            if args.verbose:
                print(f"    Window: {worker['window_name']}")
                print(f"    Pane ID: {worker['pane_id']}")
        
        alive_count = sum(1 for w in workers if w["status"] == "alive")
        dead_count = total - alive_count
        if dead_count > 0:
            print(f"\nSummary: {alive_count} alive, {dead_count} dead")
            if not args.verbose:
                print("Use --verbose for more details or 'clean' command to remove dead workers.")
        
        return 0
    else:
        error = result["error"]
        print(f"✗ Failed to get status: {error['message']}", file=sys.stderr)
        if args.verbose:
            print(f"  Error code: {error['code']}", file=sys.stderr)
        return 1


def cmd_clean(args):
    """Handle clean command."""
    result = clean_dead_workers_from_state()
    
    if result["ok"]:
        data = result["data"]
        removed = data["removed"]
        
        if removed == 0:
            print("No dead workers found to clean.")
        else:
            print(f"✓ Cleaned {removed} dead worker{'s' if removed != 1 else ''}.")
        return 0
    else:
        error = result["error"]
        print(f"✗ Failed to clean: {error['message']}", file=sys.stderr)
        if args.verbose:
            print(f"  Error code: {error['code']}", file=sys.stderr)
        return 1


def create_parser():
    """Create argument parser with all commands and options."""
    parser = argparse.ArgumentParser(
        prog='org',
        description='Orchestrate Claude Code workers in tmux sessions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start-worker /path/to/project     Start worker in directory
  %(prog)s send-command /path/to/project "ls -la"  Send command to worker
  %(prog)s status                            Show all workers status
  %(prog)s status --verbose                  Show detailed status
  %(prog)s clean                             Remove dead workers
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )
    subparsers.required = True
    
    # start-worker command
    start_parser = subparsers.add_parser(
        'start-worker',
        help='Start a Claude Code worker in the specified directory'
    )
    start_parser.add_argument(
        'directory',
        help='Directory path where to start the worker'
    )
    start_parser.set_defaults(func=cmd_start_worker)
    
    # send-command command
    send_parser = subparsers.add_parser(
        'send-command',
        help='Send a command to worker in the specified directory'
    )
    send_parser.add_argument(
        'directory',
        help='Directory path of the target worker'
    )
    send_parser.add_argument(
        'command',
        help='Command to send to the worker'
    )
    send_parser.set_defaults(func=cmd_send_command)
    
    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show status of all workers'
    )
    status_parser.set_defaults(func=cmd_status)
    
    # clean command
    clean_parser = subparsers.add_parser(
        'clean',
        help='Remove dead workers and clean state'
    )
    clean_parser.set_defaults(func=cmd_clean)
    
    return parser


def main():
    """Main entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        # Call the appropriate command function
        exit_code = args.func(args)
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()