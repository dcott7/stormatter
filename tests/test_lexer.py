from stormatter.parsing import Lexer, TokenType


def tokenize(source: str):
    return list(Lexer(source))


def test_identifier():
    tokens = tokenize("hello world")
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].to_byte_slice("hello world") == "hello"

    assert tokens[1].type == TokenType.WHITESPACE
    assert tokens[1].to_byte_slice("hello world") == " "

    assert tokens[2].type == TokenType.IDENT
    assert tokens[2].to_byte_slice("hello world") == "world"


def test_number():
    tokens = tokenize("123 456")
    assert tokens[0].type == TokenType.ICONST
    assert tokens[0].to_byte_slice("123 456") == "123"

    assert tokens[1].type == TokenType.WHITESPACE
    assert tokens[1].to_byte_slice("123 456") == " "

    assert tokens[2].type == TokenType.ICONST
    assert tokens[2].to_byte_slice("123 456") == "456"


def test_string():
    tokens = tokenize('"hello"')
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].to_byte_slice('"hello"') == '"hello"'


def test_punctuator():
    source = "(){};"
    tokens = tokenize(source)
    for i, char in enumerate(source):
        assert tokens[i].type == TokenType.PUNCTUATOR
        assert tokens[i].to_byte_slice(source) == char


def test_line_comment():
    tokens = tokenize("//this is a comment\nx")
    assert tokens[0].type == TokenType.LINECOMMENT
    assert "this is a comment" in tokens[0].to_byte_slice("//this is a comment\nx")

    assert tokens[1].type == TokenType.WHITESPACE
    assert tokens[2].type == TokenType.IDENT
    assert tokens[2].to_byte_slice("//this is a comment\nx") == "x"


def test_block_comment():
    tokens = tokenize("/*block comment*/ y")
    assert tokens[0].type == TokenType.BLOCKCOMMENT
    assert "block comment" in tokens[0].to_byte_slice("/*block comment*/ y")

    assert tokens[1].type == TokenType.WHITESPACE
    assert tokens[2].type == TokenType.IDENT
    assert tokens[2].to_byte_slice("/*block comment*/ y") == "y"


def test_eof():
    tokens = tokenize("")
    assert tokens == []


def test_only_whitespace():
    tokens = tokenize("   \t\n  ")
    assert tokens[0].type == TokenType.WHITESPACE
    assert tokens[0].to_byte_slice("   \t\n  ") == "   \t\n  "
