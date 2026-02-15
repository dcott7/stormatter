"""Paths CLI for managing paths.dat files."""

import argparse
import sys
from pathlib import Path

from ..study_manager import PathsDatManager, PathsDatHistory


def get_default_paths_dat() -> Path:
    """Get the default paths.dat in the current directory."""
    return Path.cwd() / "paths.dat"


def cmd_show(args: argparse.Namespace) -> None:
    """Show the current paths in paths.dat."""
    paths_dat = Path(args.file)
    if not paths_dat.exists():
        print(f"Error: {paths_dat} not found", file=sys.stderr)
        sys.exit(1)

    manager = PathsDatManager(paths_dat)
    paths = manager.get_paths(track_history=args.track)

    print(f"Paths from {paths_dat}:")
    for name, path in sorted(paths.items()):
        print(f"  {name}: {path}")


def cmd_make_local(args: argparse.Namespace) -> None:
    """Copy a file to local directory and update paths.dat."""
    paths_dat = Path(args.file)
    if not paths_dat.exists():
        print(f"Error: {paths_dat} not found", file=sys.stderr)
        sys.exit(1)

    dest_dir = Path(args.destination)
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True)

    manager = PathsDatManager(paths_dat)
    try:
        manager.make_local(args.name, dest_dir)
        print(f"Copied {args.name} to {dest_dir} and updated {paths_dat}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_revert(args: argparse.Namespace) -> None:
    """Revert paths.dat to previous state."""
    paths_dat = Path(args.file)
    if not paths_dat.exists():
        print(f"Error: {paths_dat} not found", file=sys.stderr)
        sys.exit(1)

    manager = PathsDatManager(paths_dat)

    if args.name:
        manager.revert_last_change_for_file(args.name)
        print(f"Reverted {args.name} in {paths_dat}")
    else:
        manager.revert_last_change()
        print(f"Reverted all entries in {paths_dat}")


def cmd_history(args: argparse.Namespace) -> None:
    """Show history for paths.dat."""
    paths_dat = Path(args.file)

    history = PathsDatHistory()
    snapshot = history.get_latest_snapshot(paths_dat)

    if not snapshot:
        print(f"No history found for {paths_dat}")
        return

    print(f"History for {paths_dat}:")
    for name in sorted(snapshot.keys()):
        last_update = history.get_last_update(paths_dat, name)
        if last_update:
            path = last_update.get("path", "")
            timestamp = last_update.get("timestamp", 0)
            import time

            ts_float = float(timestamp) if timestamp else 0.0
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts_float))
            print(f"  {name}: {path} (last updated: {time_str})")


def main() -> None:
    """Main entry point for stormatter-paths command."""
    parser = argparse.ArgumentParser(
        description="Manage paths.dat files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--file",
        default=str(get_default_paths_dat()),
        help="Path to paths.dat file (default: ./paths.dat)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # show command
    show_parser = subparsers.add_parser("show", help="Show current paths")
    show_parser.add_argument(
        "--track",
        action="store_true",
        help="Track this read in history",
    )
    show_parser.set_defaults(func=cmd_show)

    # make-local command
    local_parser = subparsers.add_parser(
        "make-local", help="Copy file to local directory and update paths.dat"
    )
    local_parser.add_argument("name", help="Name of the entry to make local")
    local_parser.add_argument(
        "destination", help="Destination directory for the copied file"
    )
    local_parser.set_defaults(func=cmd_make_local)

    # revert command
    revert_parser = subparsers.add_parser(
        "revert", help="Revert to previous paths.dat state"
    )
    revert_parser.add_argument(
        "name", nargs="?", help="Specific entry name to revert (optional)"
    )
    revert_parser.set_defaults(func=cmd_revert)

    # history command
    history_parser = subparsers.add_parser("history", help="Show history")
    history_parser.set_defaults(func=cmd_history)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
