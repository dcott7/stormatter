from dataclasses import dataclass, field


from .token import Token, TokenType


@dataclass
class Lexer:
    source: str

    current_index: int = 0
    prev_index: int = 0
    line_number: int = 1
    prev_line_number: int = 1
    byte_offset: int = 0
    prev_byte_offset: int = 0
    all_whitespace_on_this_line: bool = True

    bracket_level: int = 0
    bracket_level_stack: list[int] = field(default_factory=list)
    prev_token: Token | None = None

    def is_in_bounds(self) -> bool:
        return self.current_index < len(self.source)

    def peek(self) -> str:
        return self.source[self.current_index]

    def peek_next(self) -> str:
        assert self.current_index + 1 < len(self.source)
        return self.source[self.current_index + 1]

    def advance(self) -> None:
        self.current_index += 1
        self.byte_offset += 1

    def advance_by(self, count: int) -> None:
        self.current_index += count
        self.byte_offset += count

    def next_line(self) -> None:
        self.line_number += 1
        self.byte_offset = 0
        self.all_whitespace_on_this_line = True

    def advance_check_newline(self) -> None:
        if self.source[self.current_index] == "\n":
            self.current_index += 1
            self.next_line()
        else:
            self.advance()

    def match(self, *options: str, ignore_case: bool = False) -> bool:
        for option in options:
            if self.current_index + len(option) > len(self.source):
                continue
            snippet = self.source[self.current_index : self.current_index + len(option)]
            if ignore_case:
                option = option.lower()
                snippet = snippet.lower()
            if option == snippet:
                return True
        return False

    def make_token(self, tok_type: TokenType) -> Token:
        token = Token(
            type=tok_type,
            start_index=self.prev_index,
            end_index=self.current_index,
            start_line=self.prev_line_number,
            start_col=self.prev_byte_offset,
            end_line=self.line_number,
            end_col=self.byte_offset,
        )
        self.prev_token = token
        self.prev_index = self.current_index
        self.prev_line_number = self.line_number
        self.prev_byte_offset = self.byte_offset
        return token

    def identifier(self) -> Token:
        while self.is_in_bounds() and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        return self.make_token(TokenType.IDENT)

    def string(self) -> Token:
        self.advance()  # skip opening quote
        while self.is_in_bounds() and self.peek() != '"':
            self.advance()
        self.advance()  # skip closing quote
        return self.make_token(TokenType.STRING)

    def number(self) -> Token:
        while self.is_in_bounds() and self.peek().isdigit():
            self.advance()
        return self.make_token(TokenType.ICONST)

    def punctuator(self) -> Token:
        self.advance()
        return self.make_token(TokenType.PUNCTUATOR)

    def whitespace(self) -> Token:
        while self.is_in_bounds() and self.peek().isspace():
            self.advance()
        return self.make_token(TokenType.WHITESPACE)

    def line_comment(self) -> Token:
        if not self.match("//"):
            raise ValueError("Expected line comment")

        self.advance_by(2)  # skip //
        while self.is_in_bounds() and self.peek() not in "\r\n":
            self.advance()
        return self.make_token(TokenType.LINECOMMENT)

    def block_comment(self) -> Token:
        if not self.match("/*"):
            raise ValueError("Expected block comment")

        self.advance_by(2)  # skip /*
        while self.is_in_bounds():
            if self.match("*/"):
                self.advance_by(2)
                break
            self.advance()
        return self.make_token(TokenType.BLOCKCOMMENT)

    def eof(self) -> Token:
        return self.make_token(TokenType.EOF)

    def __iter__(self):
        return self

    def __next__(self) -> Token:
        if not self.is_in_bounds():
            raise StopIteration

        if self.match("//"):
            return self.line_comment()
        elif self.match("/*"):
            return self.block_comment()

        char = self.peek()

        if char.isspace():
            return self.whitespace()
        elif char.isalpha() or char == "_":
            return self.identifier()
        elif char.isdigit():
            return self.number()
        elif char == '"':
            return self.string()
        elif char in "{}[]();,+-*/=%<>!&|^~":
            return self.punctuator()
        else:
            self.advance()
            return self.make_token(TokenType.PUNCTUATOR)
