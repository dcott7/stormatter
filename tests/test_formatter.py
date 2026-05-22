from stormatter.parsing import Lexer
from stormatter.formatting import Formatter, FormatterConfig

mixed_case_test = """
() main() {
    // A simple program
    value x = 10;
    if (x > 5) {
        print("x is greater than 5");
    }
}
"""

dat_case_test = """
     (value) myFunction    (  value v, str s  ) {  
             
     return x;
       
       
                  }
"""


def format_source(source: str, **kwargs) -> str:  # type: ignore
    lexer = Lexer(source)
    formatter = Formatter(lexer, config=FormatterConfig(**kwargs))  # type: ignore
    return formatter.format()


def test_empty_input() -> None:
    assert format_source("", tab_display_size=4) == ""


def test_simple_indentation() -> None:
    source = "(value) main() {\n  return = 10;\n}"
    expected = "(value) main() {\n\treturn = 10;\n}"
    assert format_source(source, tab_display_size=4) == expected


def test_simple_indentation_with_spaces() -> None:
    source = "(value) main() {\n  return = 10;\n}"
    expected = "(value) main() {\n    return = 10;\n}"
    assert format_source(source, tab_display_size=4, use_tabs=False) == expected


def test_nested_indentation() -> None:
    source = "if (x > 5) {\n  if (y < 10) {\n    value z = x + y;\n  }\n}"
    expected = "if (x > 5) {\n\tif (y < 10) {\n\t\tvalue z = x + y;\n\t}\n}"
    assert format_source(source, tab_display_size=4) == expected


def test_line_comment() -> None:
    source = "// This is a comment\nvalue x = 10;"
    expected = "// This is a comment\nvalue x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_block_comment() -> None:
    source = "/* This is a\nblock comment */\nvalue x = 10;"
    expected = "/* This is a\nblock comment */\nvalue x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_string_literal() -> None:
    source = 'print("Hello, world!");'
    expected = 'print("Hello, world!");'
    assert format_source(source, tab_display_size=4) == expected


def test_integer_literal() -> None:
    source = "value x = 12345;"
    expected = "value x = 12345;"
    assert format_source(source, tab_display_size=4) == expected


def test_no_indentation() -> None:
    source = "value x = 10;"
    expected = "value x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_mixed_content() -> None:
    expected = (
        "\n() main() {\n"
        "\t// A simple program\n"
        "\tvalue x = 10;\n"
        "\tif (x > 5) {\n"
        '\t\tprint("x is greater than 5");\n'
        "\t}\n"
        "}\n"
    )
    assert format_source(mixed_case_test, tab_display_size=4) == expected


def test_dat() -> None:
    expected = "\n(value) myFunction ( value v, str s ) {\n\treturn x;\n}\n"
    assert format_source(dat_case_test, tab_display_size=4) == expected


def test_eight_space_indentation() -> None:
    source = "(value) main() {\n  return = 10;\n}"
    expected = "(value) main() {\n        return = 10;\n}"
    assert format_source(source, tab_display_size=8, use_tabs=False) == expected


def test_tab_indentation() -> None:
    source = "(value) main() {\n  return = 10;\n}"
    expected = "(value) main() {\n\treturn = 10;\n}"
    assert format_source(source, use_tabs=True) == expected


def test_section_block_indentation() -> None:
    source = "begin section\nvalue x = 10;\nend section"
    expected = "begin section\n\tvalue x = 10;\nend section"
    assert format_source(source, use_tabs=True, indent_section_blocks=True) == expected


def test_max_line_length_wraps_at_whitespace() -> None:
    source = "alpha beta"
    expected = "alpha\nbeta"
    assert format_source(source, max_line_length=8) == expected


def test_max_line_length_wraps_at_long_token() -> None:
    source = "supercalifragilisticexpialidocious"
    expected = "supercalifragilisticexpialidocious"
    assert format_source(source, max_line_length=10) == expected
