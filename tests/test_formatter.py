import pytest

from tests.util import all_data_cases, assert_format, read_data_with_mode


def check_file(subdir: str, filename: str) -> None:
    args, source, expected = read_data_with_mode(subdir, filename)
    assert_format(source, expected, **args)


@pytest.mark.parametrize("filename", all_data_cases("formatter/cases"))
def test_simple_format(filename: str) -> None:
    check_file("formatter/cases", filename)


def test_empty_input() -> None:
    assert_format("", "", tab_display_size=4)
