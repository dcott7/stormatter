from pathlib import Path

import pytest

from stormatter.study_manager.paths_parser import PathsDatParser


def test_paths_parser_basic() -> None:
    source = 'Name "/path/to/name.dat"\nName2 "/path/to/name2.dat"\n'
    parser = PathsDatParser(source)
    result = parser.parse()

    assert result["Name"] == Path("/path/to/name.dat")
    assert result["Name2"] == Path("/path/to/name2.dat")


def test_paths_parser_ignores_comments_and_whitespace() -> None:
    source = (
        'Name "/path/to/name.dat"  // comment\n'
        "\n"
        "/* block comment */\n"
        'Name2 "./relative/name2.dat"\n'
    )
    parser = PathsDatParser(source)
    result = parser.parse()

    assert result["Name"] == Path("/path/to/name.dat")
    assert result["Name2"] == Path("./relative/name2.dat").resolve()


def test_paths_parser_invalid_sequence_raises() -> None:
    source = '"/path/to/name.dat" Name\n'
    parser = PathsDatParser(source)

    with pytest.raises(ValueError):
        parser.parse()
