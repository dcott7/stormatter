"""Regenerate data/tests/result_*.dat by formatting data/tests/test.dat under
a handful of FormatterConfig settings, one setting varied at a time.

Usage:
    uv run python scripts/generate_dat_results.py
"""

from pathlib import Path

from stormatter.formatting import Formatter, FormatterConfig
from stormatter.parsing import Lexer

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "tests"
SOURCE_FILE = DATA_DIR / "test.dat"

# Each entry is (result filename suffix, FormatterConfig kwargs).
# Every case besides "default" changes exactly one setting away from the
# FormatterConfig defaults so the resulting .dat isolates that setting's effect.
CASES: dict[str, dict] = {
    "default": {},
    "tab_size": {"tab_display_size": 2},
    "use_tabs": {"use_tabs": True},
    "indent_section_blocks": {"indent_section_blocks": False},
}


def generate() -> None:
    source = SOURCE_FILE.read_text(encoding="utf-8")

    for name, config_kwargs in CASES.items():
        formatter = Formatter(
            lexer=Lexer(source), config=FormatterConfig(**config_kwargs)
        )
        formatted = formatter.format()

        result_path = DATA_DIR / f"result_{name}.dat"
        result_path.write_text(formatted, encoding="utf-8")
        print(f"Wrote {result_path.relative_to(DATA_DIR.parent.parent)}")


if __name__ == "__main__":
    generate()
