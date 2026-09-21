"""Formatter CLI for stormatter."""

import os
import sys
from multiprocessing import freeze_support
import argparse
from pathlib import Path
from typing import Sequence

from ..formatting import (
    Formatter,
    FormatterConfig,
    DEFAULT_INDENT_SECTION,
    DEFAULT_SPACES_PER_TAB,
    DEFAULT_USE_TABS,
    DEFAULT_MAX_LINE_LENGTH,
    DEFAULT_BRACE_STYLE,
    DEFAULT_EMPTY_LINES,
)
from ..parsing import Lexer
from ..utils import Cache


def default_cache_dir() -> Path:
    """Default on-disk location for the format cache (XDG-style, user-scoped)."""
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache_home) if xdg_cache_home else Path.home() / ".cache"
    return base / "stormatter"


def discover_dat_files(root: Path) -> list[Path]:
    """Recursively find all .dat files under a directory, in sorted order."""
    return sorted(root.rglob("*.dat"))


def format_source(src_code: str, config: FormatterConfig) -> str:
    """Format STORM source text and return the formatted result."""
    return Formatter(lexer=Lexer(src_code), config=config).format()


def format_path(
    file_path: Path,
    config: FormatterConfig,
    in_place: bool,
    cache: Cache | None,
) -> str:
    """Format a single file.

    Returns one of:
        "skipped"     - the cache says this file is already up to date, so it
                        was not even read.
        "unchanged"   - the file was read and formatted, but the result matched
                        what was already on disk.
        "reformatted" - the file's contents changed and (if in_place) were
                        written back.
    """
    if in_place and cache is not None and not cache.is_changed(file_path):
        return "skipped"

    src_code = file_path.read_text(encoding="utf-8")
    formatted = format_source(src_code, config)

    if not in_place:
        print(formatted)
        return "reformatted" if formatted != src_code else "unchanged"

    changed = formatted != src_code
    if changed:
        file_path.write_text(formatted, encoding="utf-8")
    if cache is not None:
        cache.update([file_path])

    return "reformatted" if changed else "unchanged"


def format_file(
    fp: str,
    tab_size: int = DEFAULT_SPACES_PER_TAB,
    use_tabs: bool = DEFAULT_USE_TABS,
    indent_section_blocks: bool = DEFAULT_INDENT_SECTION,
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH,
    brace_style: str = DEFAULT_BRACE_STYLE,
    empty_lines: str = DEFAULT_EMPTY_LINES,
    in_place: bool = True,
) -> None:
    """Format a single file and either print to stdout or write back in place."""
    config = FormatterConfig(
        tab_display_size=tab_size,
        use_tabs=use_tabs,
        indent_section_blocks=indent_section_blocks,
        max_line_length=max_line_length,
        brace_style=brace_style,
        empty_lines=empty_lines,
    )
    status = format_path(Path(fp), config, in_place, cache=None)
    if in_place and status == "reformatted":
        print(f"Formatted {fp}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for stormatter format command."""
    parser = argparse.ArgumentParser(description="Format a STORM file.")
    parser.add_argument(
        "input",
        help="Path to an input source file, or a directory to format"
        " every .dat file under it",
    )
    parser.add_argument(
        "-t",
        "--tabsize",
        type=int,
        default=DEFAULT_SPACES_PER_TAB,
        help="Number of spaces per indentation level (used only unless --tabs is set)",
    )
    parser.add_argument(
        "--tabs",
        action="store_true",
        default=DEFAULT_USE_TABS,
        help="Use tabs instead of spaces for indentation",
    )
    parser.add_argument(
        "--no-section-blocks",
        dest="section_blocks",
        action="store_false",
        default=DEFAULT_INDENT_SECTION,
        help="Do not treat 'begin IDENT' / 'end IDENT' as block delimiters",
    )
    parser.add_argument(
        "--max-line-length",
        type=int,
        default=DEFAULT_MAX_LINE_LENGTH,
        help="Wrap lines before they exceed this width when possible "
        "(0 disables wrapping)",
    )
    parser.add_argument(
        "--brace-style",
        choices=["preserve", "kr", "allman"],
        default=str(DEFAULT_BRACE_STYLE),
        help="Brace placement style to enforce",
    )
    parser.add_argument(
        "--empty-lines",
        choices=["collapse", "single", "preserve"],
        default=str(DEFAULT_EMPTY_LINES),
        help="How to handle blank lines from the source: collapse (default, "
        "never emit one), single (cap runs at one), or preserve (keep the "
        "exact count)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Print the formatted result to stdout instead of writing it back "
        "to the file. Not supported when the input is a directory.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore and do not update the on-disk format cache",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directory to store the format cache in (default: "
        "~/.cache/stormatter, or $XDG_CACHE_HOME/stormatter)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"No such file or directory: {input_path}")

    in_place = not args.test

    if input_path.is_dir():
        if not in_place:
            parser.error(
                "Formatting a directory does not support --test; printing "
                "many files to stdout isn't useful."
            )
        targets = discover_dat_files(input_path)
    else:
        targets = [input_path]

    config = FormatterConfig(
        tab_display_size=args.tabsize,
        use_tabs=args.tabs,
        indent_section_blocks=args.section_blocks,
        max_line_length=args.max_line_length,
        brace_style=args.brace_style,
        empty_lines=args.empty_lines,
    )

    cache: Cache | None = None
    if in_place and not args.no_cache:
        cache_dir = args.cache_dir or default_cache_dir()
        cache_file = cache_dir / f"cache-{config.signature()}.pickle"
        cache = Cache.load(cache_file)

    counts = {"skipped": 0, "unchanged": 0, "reformatted": 0}
    for path in targets:
        status = format_path(path, config, in_place, cache)
        counts[status] += 1
        if in_place and status == "reformatted":
            print(f"Formatted {path}", file=sys.stderr)

    if cache is not None:
        cache.save()

    if in_place and len(targets) > 1:
        print(
            f"{counts['reformatted']} reformatted, {counts['unchanged']} "
            f"unchanged, {counts['skipped']} skipped (cached)",
            file=sys.stderr,
        )


def patched_main() -> None:
    if getattr(sys, "frozen", False):
        freeze_support()
    main()


if __name__ == "__main__":
    patched_main()
