from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .token import Token, TokenType


@dataclass
class TokenStream:
    """Utility class for iterating tokens with check/expect helpers."""

    tokens: List[Token]
    source: str
    index: int = 0

    def eof(self) -> bool:
        return self.index >= len(self.tokens)

    def peek(self, offset: int = 0) -> Optional[Token]:
        idx = self.index + offset
        if idx < 0 or idx >= len(self.tokens):
            return None
        return self.tokens[idx]

    def advance(self) -> Token:
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of token stream")
        self.index += 1
        return token

    def check(
        self,
        token_type: TokenType,
        text: Optional[str] = None,
        case_sensitive: bool = True,
    ) -> bool:
        token = self.peek()
        if token is None or token.type != token_type:
            return False

        if text is None:
            return True

        token_text = token.to_byte_slice(self.source)
        if case_sensitive:
            return token_text == text
        return token_text.lower() == text.lower()

    def expect(
        self,
        token_type: TokenType,
        text: Optional[str] = None,
        case_sensitive: bool = True,
    ) -> Token:
        if not self.check(token_type, text, case_sensitive):
            got = self.peek()
            raise ValueError(
                f"Expected {token_type} {text or ''}, got {getattr(got, 'type', None)}"
            )
        return self.advance()

    def match(
        self,
        token_type: TokenType,
        text: Optional[str] = None,
        case_sensitive: bool = True,
    ) -> Optional[Token]:
        if self.check(token_type, text, case_sensitive):
            return self.advance()
        return None
