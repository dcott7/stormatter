from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    IDENT = 0
    STRING = 1
    CCONST = 2
    ICONST = 3
    FCONST = 4
    PUNCTUATOR = 5
    WHITESPACE = 6
    LINECOMMENT = 7
    BLOCKCOMMENT = 8
    EOF = 9


@dataclass
class Token:
    type: TokenType
    # Byte offsets in the file
    start_index: int
    end_index: int
    start_line: int
    # 0-indexed offset from start of line
    start_col: int
    end_line: int
    end_col: int

    def to_byte_slice(self, source: str) -> str:
        # Handle edge cases where indices may be out of bounds
        if self.start_index >= len(source) or self.end_index > len(source):
            return ""

        return source[self.start_index : self.end_index]
