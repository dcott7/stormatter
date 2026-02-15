"""Tests for the Parser ABC and token manipulation functionality."""

from stormatter.parsing import Parser, Token, TokenType


class ConcreteParser(Parser):
    """Concrete implementation of Parser for testing."""

    def parse(self) -> str:
        """Simple parse implementation for testing."""
        return self.source


def test_parser_has_lexer() -> None:
    """Test that Parser initializes with a Lexer."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    assert parser.lexer is not None
    assert parser.source == source


def test_parser_tokenize() -> None:
    """Test that Parser can tokenize source code."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens = parser.tokenize()

    assert len(tokens) > 0
    assert isinstance(tokens[0], Token)
    # Tokens should be cached
    assert parser.tokens == tokens
    assert parser._tokens_cached is True  # type: ignore


def test_parser_tokenize_caching() -> None:
    """Test that tokenize() caches results."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens1 = parser.tokenize()
    tokens2 = parser.tokenize()

    # Should return the same cached list
    assert tokens1 is tokens2


def test_parser_refresh_tokens() -> None:
    """Test that refresh_tokens() re-tokenizes."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens1 = parser.tokenize()
    parser.source = "int y = 10;"
    tokens2 = parser.refresh_tokens()

    # Should be different token lists
    assert tokens1 is not tokens2


def test_remove_comments() -> None:
    """Test removal of comment tokens."""
    source = "int x = 5; // comment\n/* block */ int y = 10;"
    parser = ConcreteParser(source)

    tokens = parser.remove_comments()

    # Should not contain any comment tokens
    for token in tokens:
        assert token.type not in [TokenType.LINECOMMENT, TokenType.BLOCKCOMMENT]

    # Should still have other tokens
    assert len(tokens) > 0

    # Verify we removed at least 2 comment tokens
    all_tokens = parser.tokenize()
    comment_count = sum(
        1
        for t in all_tokens
        if t.type in [TokenType.LINECOMMENT, TokenType.BLOCKCOMMENT]
    )
    assert comment_count == 2


def test_remove_whitespace() -> None:
    """Test removal of whitespace tokens."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens = parser.remove_whitespace()

    # Should not contain any whitespace tokens
    for token in tokens:
        assert token.type != TokenType.WHITESPACE


def test_remove_comments_and_whitespace() -> None:
    """Test removal of both comments and whitespace."""
    source = "int x = 5; // comment"
    parser = ConcreteParser(source)

    tokens = parser.remove_comments_and_whitespace()

    # Should not contain comments or whitespace
    for token in tokens:
        assert token.type not in [
            TokenType.LINECOMMENT,
            TokenType.BLOCKCOMMENT,
            TokenType.WHITESPACE,
        ]


def test_filter_tokens_exclude() -> None:
    """Test filtering tokens by exclusion."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens = parser.filter_tokens(exclude_types=[TokenType.WHITESPACE])

    for token in tokens:
        assert token.type != TokenType.WHITESPACE


def test_filter_tokens_include() -> None:
    """Test filtering tokens by inclusion."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens = parser.filter_tokens(include_types=[TokenType.IDENT])

    # Should only contain identifiers
    assert all(token.type == TokenType.IDENT for token in tokens)
    assert len(tokens) == 2  # "int" and "x"


def test_tokens_to_source() -> None:
    """Test reconstructing source from tokens."""
    source = "int x = 5;"
    parser = ConcreteParser(source)

    tokens = parser.tokenize()
    reconstructed = parser.tokens_to_source(tokens)

    assert reconstructed == source


def test_tokens_to_source_without_comments() -> None:
    """Test reconstructing source without comments."""
    source = "int x = 5; // comment"
    parser = ConcreteParser(source)

    tokens = parser.remove_comments()
    reconstructed = parser.tokens_to_source(tokens)

    assert "// comment" not in reconstructed
    assert "int x = 5;" in reconstructed


def test_reset_source() -> None:
    """Test that reset_source restores original source and clears tokens."""
    original = "int x = 5; // comment"

    parser = ConcreteParser(original)
    parser.tokenize()  # Cache some tokens

    # Modify source
    clean_tokens = parser.remove_comments()
    parser.source = parser.tokens_to_source(clean_tokens)

    assert parser._tokens_cached is True  # type: ignore

    parser.reset_source()

    assert parser.source == original
    assert parser._tokens_cached is False  # type: ignore
    assert len(parser.tokens) == 0


def test_parser_is_abstract() -> None:
    """Test that Parser cannot be instantiated directly."""
    try:
        Parser("test")  # type: ignore
        assert False, "Should not be able to instantiate Parser directly"
    except TypeError:
        pass  # Expected


def test_concrete_parser_parse() -> None:
    """Test concrete parser implementation."""
    source = "test source"
    parser = ConcreteParser(source)

    result = parser.parse()
    assert result == source
