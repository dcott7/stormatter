"""
Abstract base class for parsers with token manipulation utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from .lexer import Lexer
from .token import Token, TokenType
from .token_stream import TokenStream


class Parser(ABC):
    """
    Abstract base class for parsers.

    Provides common functionality for parsing source code,
    including lexical analysis and token filtering utilities.
    """

    def __init__(self, source: str) -> None:
        """
        Initialize the parser.

        Args:
            source: The source code to parse
        """
        self.source = source
        self.original_source = source
        self.lexer = Lexer(source)
        self.tokens: List[Token] = []
        self._tokens_cached = False

    def tokenize(self) -> List[Token]:
        """
        Tokenize the source code using the Lexer.

        Returns:
            List of tokens from the source code

        Note:
            Tokens are cached after first call. Use refresh_tokens() to re-tokenize.
        """
        if not self._tokens_cached:
            self.tokens = list(self.lexer)
            self._tokens_cached = True
        return self.tokens

    def refresh_tokens(self) -> List[Token]:
        """
        Force re-tokenization of the current source.

        Returns:
            List of tokens from the source code
        """
        self.lexer = Lexer(self.source)
        self._tokens_cached = False
        return self.tokenize()

    @abstractmethod
    def parse(self) -> Any:
        """
        Parse the source code.

        Must be implemented by subclasses.
        """
        pass

    def filter_tokens(
        self,
        exclude_types: Optional[List[TokenType]] = None,
        include_types: Optional[List[TokenType]] = None,
    ) -> List[Token]:
        """
        Filter tokens by type.

        Args:
            exclude_types: Token types to exclude from the result
            include_types: Token types to include (if provided, only these are included)

        Returns:
            Filtered list of tokens

        Note:
            If both exclude_types and include_types are provided, include_types takes precedence.

        Example:
            >>> # Remove comments
            >>> tokens = parser.filter_tokens(exclude_types=[TokenType.LINECOMMENT, TokenType.BLOCKCOMMENT])
            >>> # Get only identifiers
            >>> tokens = parser.filter_tokens(include_types=[TokenType.IDENT])
        """
        tokens = self.tokenize()

        if include_types is not None:
            return [t for t in tokens if t.type in include_types]

        if exclude_types is not None:
            return [t for t in tokens if t.type not in exclude_types]

        return tokens.copy()

    def remove_comments(self) -> List[Token]:
        """
        Remove comment tokens from the token stream.

        Returns:
            List of tokens without LINECOMMENT and BLOCKCOMMENT tokens

        Example:
            >>> parser = ConcreteParser("int x = 5; // comment")
            >>> tokens = parser.remove_comments()
            >>> # tokens will not contain comment tokens
        """
        return self.filter_tokens(
            exclude_types=[TokenType.LINECOMMENT, TokenType.BLOCKCOMMENT]
        )

    def remove_whitespace(self) -> List[Token]:
        """
        Remove whitespace tokens from the token stream.

        Returns:
            List of tokens without WHITESPACE tokens
        """
        return self.filter_tokens(exclude_types=[TokenType.WHITESPACE])

    def remove_comments_and_whitespace(self) -> List[Token]:
        """
        Remove both comment and whitespace tokens from the token stream.

        Returns:
            List of tokens without LINECOMMENT, BLOCKCOMMENT, or WHITESPACE tokens
        """
        return self.filter_tokens(
            exclude_types=[
                TokenType.LINECOMMENT,
                TokenType.BLOCKCOMMENT,
                TokenType.WHITESPACE,
            ]
        )

    def tokens_to_source(self, tokens: Optional[List[Token]] = None) -> str:
        """
        Reconstruct source code from tokens.

        Args:
            tokens: List of tokens to reconstruct. If None, uses self.tokens

        Returns:
            Reconstructed source code string

        Example:
            >>> parser = ConcreteParser("int x = 5; // comment")
            >>> clean_tokens = parser.remove_comments()
            >>> clean_source = parser.tokens_to_source(clean_tokens)
            >>> # clean_source will be "int x = 5; " without the comment
        """
        if tokens is None:
            tokens = self.tokens

        if not tokens:
            return ""

        result: List[str] = []
        for token in tokens:
            result.append(token.to_byte_slice(self.source))

        return "".join(result)

    def token_stream(self, tokens: Optional[List[Token]] = None) -> TokenStream:
        """
        Create a TokenStream for iterating with check/expect helpers.

        Args:
            tokens: Optional token list. If None, uses tokenize().

        Returns:
            TokenStream instance
        """
        if tokens is None:
            tokens = self.tokenize()
        return TokenStream(tokens=tokens, source=self.source)

    def reset_source(self) -> None:
        """Reset the source to the original source code and clear cached tokens."""
        self.source = self.original_source
        self.lexer = Lexer(self.original_source)
        self._tokens_cached = False
        self.tokens = []
