import unittest

from stormatter.lexer import Lexer
from stormatter.formatter import Formatter


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


class TestFormatter(unittest.TestCase):

    def test_empty_input(self):
        lexer = Lexer("")
        formatter = Formatter(lexer, tab_display_size=4)
        self.assertEqual(formatter.format(), "")

    def test_simple_indentation(self):
        source_code = "int main() {\n  int x = 10;\n}"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "int main() {\n\tint x = 10;\n}"
        self.assertEqual(formatter.format(), expected_output)

    def test_nested_indentation(self):
        source_code = "if (x > 5) {\n  if (y < 10) {\n    int z = x + y;\n  }\n}"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "if (x > 5) {\n\tif (y < 10) {\n\t\tint z = x + y;\n\t}\n}"
        self.assertEqual(formatter.format(), expected_output)

    def test_line_comment(self):
        source_code = "// This is a comment\nint x = 10;"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "// This is a comment\nint x = 10;"
        self.assertEqual(formatter.format(), expected_output)

    def test_block_comment(self):
        source_code = "/* This is a\nblock comment */\nint x = 10;"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "/* This is a\nblock comment */\nint x = 10;"
        self.assertEqual(formatter.format(), expected_output)

    def test_string_literal(self):
        source_code = 'print("Hello, world!");'
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = 'print("Hello, world!");'
        self.assertEqual(formatter.format(), expected_output)

    def test_integer_literal(self):
        source_code = "int x = 12345;"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "int x = 12345;"
        self.assertEqual(formatter.format(), expected_output)

    def test_no_indentation(self):
        source_code = "int x = 10;"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "int x = 10;"
        self.assertEqual(formatter.format(), expected_output)

    def test_mixed_content(self):
        source_code = mixed_case_test
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = '\nint main() {\n\t// A simple program\n\tint x = 10;\n\tif (x > 5) {\n\t\tprint("x is greater than 5");\n\t}\n}\n'
        self.assertEqual(formatter.format(), expected_output)

    def test_dat(self):
        source_code = dat_case_test
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=4)
        expected_output = "\nvalue myFunction ( value v, str s ) {\n\treturn x;\n}\n"
        self.assertEqual(formatter.format(), expected_output)

    def test_eight_space_indentation(self):
        source_code = "int main() {\n  int x = 10;\n}"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, tab_display_size=8, use_tabs=False)
        expected_output = "int main() {\n        int x = 10;\n}"
        self.assertEqual(formatter.format(), expected_output)

    def test_tab_indentation(self):
        source_code = "int main() {\n  int x = 10;\n}"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, use_tabs=True)
        expected_output = "int main() {\n\tint x = 10;\n}"
        self.assertEqual(formatter.format(), expected_output)

    def test_section_block_indentation(self):
        source_code = "begin section\nvalue x = 10;\nend section"
        lexer = Lexer(source_code)
        formatter = Formatter(lexer, use_tabs=True, indent_section_blocks=True)
        expected_output = "begin section\n\tvalue x = 10;\nend section"
        self.assertEqual(formatter.format(), expected_output)


if __name__ == "__main__":
    unittest.main()
