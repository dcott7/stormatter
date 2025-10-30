import unittest


from stormatter.lexer import Lexer
from stormatter.token import TokenType


class TestLexer(unittest.TestCase):

    def tokenize(self, source):
        lexer = Lexer(source)
        return list(lexer)

    def test_identifier(self):
        tokens = self.tokenize("hello world")
        self.assertEqual(tokens[0].type, TokenType.IDENT)
        self.assertEqual(tokens[0].to_byte_slice("hello world"), "hello")
        self.assertEqual(tokens[1].type, TokenType.WHITESPACE)
        self.assertEqual(tokens[1].to_byte_slice("hello world"), " ")
        self.assertEqual(tokens[2].type, TokenType.IDENT)
        self.assertEqual(tokens[2].to_byte_slice("hello world"), "world")

    def test_number(self):
        tokens = self.tokenize("123 456")
        self.assertEqual(tokens[0].type, TokenType.ICONST)
        self.assertEqual(tokens[0].to_byte_slice("123 456"), "123")
        self.assertEqual(tokens[1].type, TokenType.WHITESPACE)
        self.assertEqual(tokens[1].to_byte_slice("123 456"), " ")
        self.assertEqual(tokens[2].type, TokenType.ICONST)
        self.assertEqual(tokens[2].to_byte_slice("123 456"), "456")

    def test_string(self):
        tokens = self.tokenize('"hello"')
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].to_byte_slice('"hello"'), '"hello"')

    def test_punctuator(self):
        source = "(){};"
        tokens = self.tokenize(source)
        expected = list(source)
        for i, char in enumerate(expected):
            self.assertEqual(tokens[i].type, TokenType.PUNCTUATOR)
            self.assertEqual(tokens[i].to_byte_slice(source), char)

    def test_line_comment(self):
        tokens = self.tokenize("//this is a comment\nx")
        self.assertEqual(tokens[0].type, TokenType.LINECOMMENT)
        self.assertIn(
            "this is a comment",
            tokens[0].to_byte_slice("//this is a comment\nx"),
        )
        self.assertEqual(tokens[1].type, TokenType.WHITESPACE)
        self.assertEqual(tokens[2].type, TokenType.IDENT)
        self.assertEqual(tokens[2].to_byte_slice("//this is a comment\nx"), "x")

    def test_block_comment(self):
        tokens = self.tokenize("/*block comment*/ y")
        self.assertEqual(tokens[0].type, TokenType.BLOCKCOMMENT)
        self.assertIn("block comment", tokens[0].to_byte_slice("/*block comment*/ y"))
        self.assertEqual(tokens[1].type, TokenType.WHITESPACE)
        self.assertEqual(tokens[2].type, TokenType.IDENT)
        self.assertEqual(tokens[2].to_byte_slice("/*block comment*/ y"), "y")

    def test_eof(self):
        tokens = self.tokenize("")
        self.assertEqual(tokens, [])

    def test_only_whitespace(self):
        tokens = self.tokenize("   \t\n  ")
        self.assertEqual(tokens[0].type, TokenType.WHITESPACE)
        self.assertEqual(tokens[0].to_byte_slice("   \t\n  "), "   \t\n  ")


if __name__ == "__main__":
    unittest.main()
