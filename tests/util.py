import json
import re
from pathlib import Path
from typing import Any

from stormatter.formatting import Formatter, FormatterConfig
from stormatter.parsing import Lexer

TESTS_DIR = Path(__file__).parent
DATA_DIR = TESTS_DIR / "data"


def all_data_cases(subdir: str) -> list[str]:
    """Return a list of all test case filenames (without extension) in the given subdir."""
    case_dir = DATA_DIR / subdir
    return sorted(path.stem for path in case_dir.glob("*.case"))


def read_data_with_mode(subdir: str, filename: str) -> tuple[dict[str, Any], str, str]:
    """Read a test case file and return options, source, and expected output."""
    case_dir = DATA_DIR / subdir
    case_path = case_dir / f"{filename}.case"
    case_text = case_path.read_text(encoding="utf-8")

    options: dict[str, Any] = {}
    if case_text.startswith("# options:"):
        options_line, remainder = case_text.split("\n", 1)
        options = json.loads(options_line.removeprefix("# options:").strip())
        case_text = remainder

    match = re.search(r"(?m)^# output[ \t]*$", case_text)
    if match is None:
        raise ValueError(f"Missing '# output' marker in case file: {case_path}")

    source = case_text[: match.start()]
    if source.endswith("\n"):
        source = source[:-1]

    expected = case_text[match.end() :]
    if expected.startswith("\n"):
        expected = expected[1:]

    return options, source, expected


def assert_format(source: str, expected: str, **kwargs: Any) -> None:
    """Assert that formatting the source code produces the expected output."""
    formatter = Formatter(lexer=Lexer(source), config=FormatterConfig(**kwargs))
    assert formatter.format() == expected
