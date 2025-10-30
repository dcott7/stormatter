import sys
from multiprocessing import freeze_support
import argparse

from .formatter import Formatter
from .lexer import Lexer


def format_file(
    fp: str,
    tab_size: int = 4,
    use_tabs: bool = True,
    indent_section_blocks: bool = False,
) -> None:
    with open(fp, "r", encoding="utf-8") as f:
        src_code = f.read()

    formatter = Formatter(
        lexer=Lexer(src_code),
        tab_display_size=tab_size,
        use_tabs=use_tabs,
        indent_section_blocks=indent_section_blocks,
    )

    print(formatter.format())


def main():
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

    args = parser.parse_args()
    format_file(
        args.input,
        tab_size=args.tabsize,
        use_tabs=not args.spaces,
        indent_section_blocks=args.section_blocks,
    )


def patched_main() -> None:
    """Mimic Black’s entrypoint for PyInstaller compatibility."""
    if getattr(sys, "frozen", False):
        freeze_support()
    main()


if __name__ == "__main__":
    patched_main()
