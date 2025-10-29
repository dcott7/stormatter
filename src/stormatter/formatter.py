from dataclasses import dataclass, field
from typing import List


from .lexer import Lexer
from .token import Token, TokenType


@dataclass
class Formatter:
    lexer: Lexer
    tab_display_size: int = 4
    use_tabs: bool = True
    indent_section_blocks: bool = False  # flag to indent/dedent on begin/end
    indent_level: int = 0
    output: str = ""
    tokens: List[Token] = field(default_factory=list)
    current_token_index: int = 0
    dedent_accounted_for = False

    def __post_init__(self):
        # pre-tokenize the entire input
        self.tokens = list(self.lexer)
        self.current_token_index = 0

    def peek_token(self, offset: int = 0) -> Token | None:
        """Peeks at a token ahead of the current token."""
        index = self.current_token_index + offset
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    def consume_token(self) -> Token:
        """Consumes and returns the next token."""
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        else:
            # handle reaching the end of tokens gracefully by returning EOF
            return Token(TokenType.EOF, 0, 0, 0, 0, 0, 0)

    def emit(self, text: str) -> None:
        """Appends text to the output."""
        self.output += text

    def emit_indent(self) -> None:
        """Emits indentation based on the current indent level."""
        if self.use_tabs:
            self.emit("\t" * self.indent_level)
        else:
            self.emit(" " * self.indent_level * self.tab_display_size)

    def format(self) -> str:
        """Formats the code based on the token stream."""
        while self.current_token_index < len(self.tokens):
            token = self.consume_token()
            token_text = self.lexer.source[token.start_index : token.end_index]
            # print(f'{repr(token_text)} {self.indent_level}')

            if token.type == TokenType.WHITESPACE:
                # normalize to single spaces, or newlines with indentation
                if "\n" in token_text:
                    self.emit("\n")
                    next_token = self.peek_token()
                    if next_token and (
                        (
                            next_token.type == TokenType.PUNCTUATOR
                            and self.lexer.source[
                                next_token.start_index : next_token.end_index
                            ]
                            in ["}", "]", ")"]
                        )
                        or (
                            self.indent_section_blocks
                            and next_token.type == TokenType.IDENT
                            and self.lexer.source[
                                next_token.start_index : next_token.end_index
                            ].lower()
                            == "end"
                        )
                    ):
                        # reduce the indent PRIOR to consuming the dedent token
                        self.indent_level = max(0, self.indent_level - 1)
                        self.dedent_accounted_for = (
                            True  # flag for early dedent handling
                        )
                    self.emit_indent()
                else:
                    self.emit(" ")  # default to just a space

            elif token.type == TokenType.IDENT:
                if not self.indent_section_blocks:
                    self.emit(token_text)
                    continue

                offset = 1
                # Find the next non-whitespace token
                next_token = self.peek_token(offset)
                while next_token and next_token.type == TokenType.WHITESPACE:
                    offset += 1
                    next_token = self.peek_token(offset)

                if next_token and next_token.type == TokenType.IDENT:
                    next_text = self.lexer.source[
                        next_token.start_index : next_token.end_index
                    ]

                    if token_text.lower() == "begin":
                        self.emit(token_text + " " + next_text)
                        # Consume all tokens up to and including the second IDENT
                        for _ in range(offset):
                            self.consume_token()
                        self.consume_token()  # consume the second IDENT itself
                        self.indent_level += 1
                        continue

                    elif token_text.lower() == "end":
                        if not self.dedent_accounted_for:
                            self.indent_level = max(0, self.indent_level - 1)
                        self.dedent_accounted_for = False
                        self.emit(token_text + " " + next_text)
                        for _ in range(offset):
                            self.consume_token()
                        self.consume_token()  # consume the second IDENT itself
                        continue

                self.emit(token_text)

            elif token.type == TokenType.STRING:
                self.emit(token_text)
            elif token.type == TokenType.ICONST:
                self.emit(token_text)
            elif token.type == TokenType.FCONST:
                self.emit(token_text)
            elif token.type == TokenType.PUNCTUATOR:
                # basic indentation handling based on braces.
                if token_text in ["{", "[", "("]:
                    self.emit(token_text)  # emit this token before updating indentation
                    self.indent_level += 1
                elif token_text in ["}", "]", ")"]:
                    if not self.dedent_accounted_for:
                        self.indent_level = max(0, self.indent_level - 1)
                    self.dedent_accounted_for = False
                    self.emit(token_text)  # emit this token after updating indentation
                else:
                    self.emit(
                        token_text
                    )  # punctuator does not cause a change in indentation level

            elif token.type == TokenType.LINECOMMENT:
                self.emit(token_text)

            elif token.type == TokenType.BLOCKCOMMENT:
                self.emit(token_text)

            elif token.type == TokenType.EOF:
                break  # stop formatting at EOF

            else:
                self.emit(token_text)  # fallback

        return self.output
