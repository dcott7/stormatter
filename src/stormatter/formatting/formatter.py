from dataclasses import dataclass, field
from typing import List

from ..parsing.lexer import Lexer
from ..parsing.token import Token, TokenType


@dataclass
class FormattedTokenOutput:
    token_type: TokenType
    text: str


@dataclass
class Formatter:
    """
    A code formatter that processes a stream of tokens and outputs formatted code.

    Attributes:
        lexer (Lexer): The lexer providing the token stream.
        tab_display_size (int): Number of spaces per tab if spaces are used for indentation.
        use_tabs (bool): Whether to use tabs for indentation.
        indent_section_blocks (bool): Whether to indent/dedent on 'begin'/'end' keywords.
        indent_level (int): Current indentation level.
        output_strs: List[FormattedTokenOutput]: The formatted output as a list of FormattedTokenOutput instances.
        tokens (List[Token]): List of tokens from the lexer.
        current_token_index (int): Index of the current token being processed.
        dedent_accounted_for (bool): Flag to track if dedent has been handled.
    Methods:
        format() -> str: Formats the code based on the token stream and returns the formatted string.
    """

    lexer: Lexer
    tab_display_size: int = 4
    use_tabs: bool = True
    indent_section_blocks: bool = False  # flag to indent/dedent on begin/end
    indent_level: int = 0
    output_strs: List[FormattedTokenOutput] = field(default_factory=lambda: [])
    tokens: List[Token] = field(default_factory=lambda: [])
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

    def emit(self, token_type: TokenType, text: str) -> None:
        """Appends text to the output."""
        self.output_strs.append(FormattedTokenOutput(token_type, text))

    def emit_indent(self) -> None:
        """Emits indentation based on the current indent level."""
        if self.use_tabs:
            self.emit(TokenType.WHITESPACE, "\t" * self.indent_level)
        else:
            self.emit(
                TokenType.WHITESPACE, " " * self.indent_level * self.tab_display_size
            )

    def format_tokens(self) -> List[FormattedTokenOutput]:
        """Formats the tokens and returns a list of formatted tokens."""
        while self.current_token_index < len(self.tokens):
            token = self.consume_token()  # get the next token
            token_text = self.lexer.source[token.start_index : token.end_index]
            # print(f'{repr(token_text)} {self.indent_level}')

            if token.type == TokenType.WHITESPACE:
                # if the whitespace contains a newline then we need to check what
                # the next token is. If the next token is a token that causes a dedent,
                # we need to reduce the indent level PRIOR to emitting this dedent causing
                # token. If we did not do this, the dedent token would be indented cause the
                # following newline to emit the indent at the current level. For example:
                #    {
                #       '\n' causes indent emit here
                #    }  <- this closing brace would be indented incorrectly
                # Handle multiple newlines by only emitting one and ignoring the rest. This
                # causes some loss of fidelity but keeps things simple for now. Block comments
                # containing multiple newlines will be preserved while formatting.
                if "\n" in token_text:
                    self.emit(TokenType.WHITESPACE, "\n")
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
                    self.emit(TokenType.WHITESPACE, " ")  # default to just a space

            elif token.type == TokenType.IDENT:
                # We have hit an identifier. Check if it's 'begin' or 'end' for special handling.
                # If the identifier is 'begin' we will increase the indent level after emitting the
                # 'begin', a ' ' and the next identifier token. If the identifier is 'end' we will
                # decrease the indent level before emitting. This only applies if the
                # indent_section_blocks flag is set to True. If the next token is not an IDENT we
                # just emit the current IDENT normally. If the ident is 'end' and we have already
                # accounted for a dedent due to a preceding newline, we do not reduce the indent
                # level again we just reset the dedent_accounted_for flag and emit normally.
                if not self.indent_section_blocks:
                    self.emit(TokenType.IDENT, token_text)
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
                        self.emit(TokenType.IDENT, token_text + " " + next_text)
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
                        self.emit(TokenType.IDENT, token_text + " " + next_text)
                        for _ in range(offset):
                            self.consume_token()
                        self.consume_token()  # consume the second IDENT itself
                        continue

                self.emit(TokenType.IDENT, token_text)

            elif token.type == TokenType.STRING:
                self.emit(TokenType.STRING, token_text)
            elif token.type == TokenType.ICONST:
                self.emit(TokenType.ICONST, token_text)
            elif token.type == TokenType.FCONST:
                self.emit(TokenType.FCONST, token_text)
            elif token.type == TokenType.PUNCTUATOR:
                # basic indentation handling based on braces.
                if token_text in ["{", "[", "("]:
                    self.emit(
                        TokenType.PUNCTUATOR, token_text
                    )  # emit this token before updating indentation
                    self.indent_level += 1
                elif token_text in ["}", "]", ")"]:
                    if not self.dedent_accounted_for:
                        self.indent_level = max(0, self.indent_level - 1)
                    self.dedent_accounted_for = False
                    self.emit(
                        TokenType.PUNCTUATOR, token_text
                    )  # emit this token after updating indentation
                else:
                    self.emit(
                        TokenType.PUNCTUATOR, token_text
                    )  # punctuator does not cause a change in indentation level

            elif token.type == TokenType.LINECOMMENT:
                self.emit(TokenType.LINECOMMENT, token_text)

            elif token.type == TokenType.BLOCKCOMMENT:
                self.emit(TokenType.BLOCKCOMMENT, token_text)

            elif token.type == TokenType.EOF:
                break  # stop formatting at EOF

            else:
                self.emit(token.type, token_text)  # fallback

        return self.output_strs

    def format(self) -> str:
        """Formats the code based on the token stream."""
        formatted_tokens = self.format_tokens()
        return "".join(token_output.text for token_output in formatted_tokens)
