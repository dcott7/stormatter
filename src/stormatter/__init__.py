"""Stormatter - A code formatter and study manager for STORM files."""

from .formatting import Formatter
from .parsing import Lexer


# Legacy format_file function for backwards compatibility
def format_file(
    fp: str,
    tab_size: int = 4,
    use_tabs: bool = True,
    indent_section_blocks: bool = False,
) -> None:
    """Format a file and print to stdout. (Legacy function, use CLI instead)"""
    with open(fp, "r", encoding="utf-8") as f:
        src_code = f.read()

    formatter = Formatter(
        lexer=Lexer(src_code),
        tab_display_size=tab_size,
        use_tabs=use_tabs,
        indent_section_blocks=indent_section_blocks,
    )

    print(formatter.format())


# Legacy main function - now just imports from cli.format
def main():
    """Legacy main function - redirects to cli.format.main()"""
    from .cli.format import main as format_main

    format_main()


def patched_main() -> None:
    """Legacy patched_main - redirects to cli.format.patched_main()"""
    from .cli.format import patched_main as format_patched_main

    format_patched_main()


if __name__ == "__main__":
    patched_main()
