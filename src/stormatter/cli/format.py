"""Formatter CLI for stormatter."""

import sys
from multiprocessing import freeze_support
import argparse
from pathlib import Path

from ..formatting import Formatter
from ..parsing import Lexer


def format_file(
    fp: str,
    tab_size: int = 4,
    use_tabs: bool = True,
    indent_section_blocks: bool = False,
    in_place: bool = False,
) -> None:
    """Format a file and either print to stdout or write back in place."""
    file_path = Path(fp)
    src_code = file_path.read_text(encoding="utf-8")

    formatter = Formatter(
        lexer=Lexer(src_code),
        tab_display_size=tab_size,
        use_tabs=use_tabs,
        indent_section_blocks=indent_section_blocks,
    )

    formatted = formatter.format()

    if in_place:
        file_path.write_text(formatted, encoding="utf-8")
        print(f"Formatted {fp}", file=sys.stderr)
    else:
        print(formatted)


def main() -> None:
    """Main entry point for stormatter format command."""
    parser = argparse.ArgumentParser(description="Format a STORM file.")
    parser.add_argument("input", help="Path to the input source file")
    parser.add_argument(
        "-t",
        "--tabsize",
        type=int,
        default=4,
        help="Number of spaces per indentation level (used only if --spaces is set)",
    )
    parser.add_argument(
        "--spaces",
        action="store_true",
        help="Use spaces instead of tabs for indentation",
    )
    parser.add_argument(
        "--section-blocks",
        action="store_true",
        help="Treat 'begin IDENT' / 'end IDENT' as block delimiters",
    )
    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Format file in place instead of printing to stdout",
    )

    args = parser.parse_args()
    format_file(
        args.input,
        tab_size=args.tabsize,
        use_tabs=not args.spaces,
        indent_section_blocks=args.section_blocks,
        in_place=args.in_place,
    )


def patched_main() -> None:
    """Mimic Black's entrypoint for PyInstaller compatibility."""
    if getattr(sys, "frozen", False):
        freeze_support()
    main()


if __name__ == "__main__":
    patched_main()
