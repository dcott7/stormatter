from stormatter.parsing import Lexer
from stormatter.formatting import Formatter


mixed_case_test = """
int main() {
    // A simple program
    int x = 10;
    if (x > 5) {
        print("x is greater than 5");
    }
}
"""

dat_case_test = """
     value myFunction    (  value v, str s  ) {  
             
     return x;
       
       
                  }
"""


def format_source(source: str, **kwargs):  # type: ignore
    lexer = Lexer(source)
    formatter = Formatter(lexer, **kwargs)  # type: ignore
    return formatter.format()


def test_empty_input():
    assert format_source("", tab_display_size=4) == ""


def test_simple_indentation():
    source = "int main() {\n  int x = 10;\n}"
    expected = "int main() {\n\tint x = 10;\n}"
    assert format_source(source, tab_display_size=4) == expected


def test_nested_indentation():
    source = "if (x > 5) {\n  if (y < 10) {\n    int z = x + y;\n  }\n}"
    expected = "if (x > 5) {\n\tif (y < 10) {\n\t\tint z = x + y;\n\t}\n}"
    assert format_source(source, tab_display_size=4) == expected


def test_line_comment():
    source = "// This is a comment\nint x = 10;"
    expected = "// This is a comment\nint x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_block_comment():
    source = "/* This is a\nblock comment */\nint x = 10;"
    expected = "/* This is a\nblock comment */\nint x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_string_literal():
    source = 'print("Hello, world!");'
    expected = 'print("Hello, world!");'
    assert format_source(source, tab_display_size=4) == expected


def test_integer_literal():
    source = "int x = 12345;"
    expected = "int x = 12345;"
    assert format_source(source, tab_display_size=4) == expected


def test_no_indentation():
    source = "int x = 10;"
    expected = "int x = 10;"
    assert format_source(source, tab_display_size=4) == expected


def test_mixed_content():
    expected = (
        "\nint main() {\n"
        "\t// A simple program\n"
        "\tint x = 10;\n"
        "\tif (x > 5) {\n"
        '\t\tprint("x is greater than 5");\n'
        "\t}\n"
        "}\n"
    )
    assert format_source(mixed_case_test, tab_display_size=4) == expected


def test_dat():
    expected = "\nvalue myFunction ( value v, str s ) {\n\treturn x;\n}\n"
    assert format_source(dat_case_test, tab_display_size=4) == expected


def test_eight_space_indentation():
    source = "int main() {\n  int x = 10;\n}"
    expected = "int main() {\n        int x = 10;\n}"
    assert format_source(source, tab_display_size=8, use_tabs=False) == expected


def test_tab_indentation():
    source = "int main() {\n  int x = 10;\n}"
    expected = "int main() {\n\tint x = 10;\n}"
    assert format_source(source, use_tabs=True) == expected


def test_section_block_indentation():
    source = "begin section\nvalue x = 10;\nend section"
    expected = "begin section\n\tvalue x = 10;\nend section"
    assert format_source(source, use_tabs=True, indent_section_blocks=True) == expected
