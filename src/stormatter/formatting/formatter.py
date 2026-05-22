from dataclasses import dataclass, field
import logging
from typing import List

from ..parsing.lexer import Lexer
from ..parsing.token import Token, TokenType

logger = logging.getLogger(__name__)


@dataclass
class FormattedTokenOutput:
    token_type: TokenType
    text: str


@dataclass
class FormatterConfig:
    """
    Configuration options for the Formatter.

    Attributes:
        tab_display_size (int): Number of spaces per tab if spaces are used for indentation.
        use_tabs (bool): Whether to use tabs for indentation.
        indent_section_blocks (bool): Whether to indent/dedent on 'begin'/'end'
        max_line_length (int | None): Optional maximum display width for a line.
        brace_style (str): Brace placement style: 'preserve', 'kr', or 'allman'.
    """

    tab_display_size: int = 4
    use_tabs: bool = True
    indent_section_blocks: bool = False
    max_line_length: int | None = None
    brace_style: str = "preserve"


@dataclass
class Formatter:
    """
    A code formatter that processes a stream of tokens and outputs formatted code.

    Attributes:
        lexer (Lexer): The lexer providing the token stream.
        config (FormatterConfig): Configuration options for the formatter.
        indent_level (int): Current indentation level.
        output_strs: List[FormattedTokenOutput]: The formatted output as a list of FormattedTokenOutput instances.
        tokens (List[Token]): List of tokens from the lexer.
        current_token_index (int): Index of the current token being processed.
        dedent_accounted_for (bool): Flag to track if dedent has been handled.
    Methods:
        format() -> str: Formats the code based on the token stream and returns the formatted string.
    """

    lexer: Lexer
    config: FormatterConfig = field(default_factory=FormatterConfig)
    indent_level: int = 0
    output_strs: List[FormattedTokenOutput] = field(default_factory=lambda: [])
    tokens: List[Token] = field(default_factory=lambda: [])
    current_token_index: int = 0
    current_line_length: int = 0
    dedent_accounted_for = False

    def __post_init__(self):
        # pre-tokenize the entire input
        self.tokens = list(self.lexer)
        self.current_token_index = 0
        self.current_line_length = 0
        logger.debug(
            "Formatter initialized: tokens=%d, tab_display_size=%d, use_tabs=%s, "
            "indent_section_blocks=%s, max_line_length=%s, brace_style=%s",
            len(self.tokens),
            self.config.tab_display_size,
            self.config.use_tabs,
            self.config.indent_section_blocks,
            self.config.max_line_length,
            self.config.brace_style,
        )

        if self.config.brace_style not in ["preserve", "kr", "allman"]:
            raise ValueError(
                "brace_style must be one of: 'preserve', 'kr', or 'allman'"
            )

    def describe_token(self, token: Token | None) -> str:
        """Builds a concise debug description of a token."""
        if token is None:
            return "None"

        token_text = self.token_text(token)
        return (
            f"{token.type.name}({token_text!r}) "
            f"@ {token.start_line}:{token.start_col}-{token.end_line}:{token.end_col}"
        )

    def token_text(self, token: Token) -> str:
        """Returns the source text covered by a token."""
        return self.lexer.source[token.start_index : token.end_index]

    def text_width(self, text: str) -> int:
        """Returns the display width of text on its last line."""
        width = 0
        for char in text:
            if char == "\n":
                width = 0
            elif char == "\t":
                width += self.config.tab_display_size
            else:
                width += 1
        return width

    def update_line_length(self, text: str) -> None:
        """Updates the tracked display width for the current output line."""
        previous_length = self.current_line_length
        if "\n" in text:
            self.current_line_length = self.text_width(text.split("\n")[-1])
        else:
            self.current_line_length += self.text_width(text)
        logger.debug(
            "Line length updated: %d -> %d after emitting %r",
            previous_length,
            self.current_line_length,
            text,
        )

    def next_non_whitespace_token(self, offset: int = 0) -> Token | None:
        """Returns the next non-whitespace token after the current token."""
        next_token = self.peek_token(offset)
        while next_token and next_token.type == TokenType.WHITESPACE:
            offset += 1
            next_token = self.peek_token(offset)
        return next_token

    def token_causes_dedent(self, token: Token) -> bool:
        """Checks whether a token should reduce indentation after a line break."""
        token_text = self.token_text(token)
        return (
            token.type == TokenType.PUNCTUATOR and token_text in ["}", "]", ")"]
        ) or (
            self.config.indent_section_blocks
            and token.type == TokenType.IDENT
            and token_text.lower() == "end"
        )

    def is_opening_brace(self, token: Token | None) -> bool:
        """Checks whether a token is an opening curly brace."""
        return (
            token is not None
            and token.type == TokenType.PUNCTUATOR
            and self.token_text(token) == "{"
        )

    def should_wrap_before(self, token: Token | None) -> bool:
        """Checks whether the next token should move onto a new line."""
        if token is None:
            return False

        if not self.config.max_line_length or self.config.max_line_length <= 0:
            return False

        if token.type == TokenType.WHITESPACE:
            return False

        if self.current_line_length == 0:
            return False

        token_length = self.text_width(self.token_text(token))
        projected_length = self.current_line_length + 1 + token_length
        should_wrap = projected_length > self.config.max_line_length
        logger.debug(
            "Wrap check: line_length=%d, token=%s, token_len=%d, projected=%d, "
            "limit=%d, wrap=%s",
            self.current_line_length,
            self.describe_token(token),
            token_length,
            projected_length,
            self.config.max_line_length,
            should_wrap,
        )
        return should_wrap

    def emit_line_break(self, next_token: Token | None) -> None:
        """Emits a normalized newline and the indentation for the next line."""
        logger.debug(
            "Emitting normalized line break before token %s",
            self.describe_token(next_token),
        )
        self.emit(TokenType.WHITESPACE, "\n")
        if next_token and self.token_causes_dedent(next_token):
            previous_indent = self.indent_level
            self.indent_level = max(0, self.indent_level - 1)
            self.dedent_accounted_for = True
            logger.debug(
                "Applied early dedent during line break: %d -> %d",
                previous_indent,
                self.indent_level,
            )
        self.emit_indent()

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
            logger.debug(
                "Consumed token[%d]: %s",
                self.current_token_index - 1,
                self.describe_token(token),
            )
            return token
        else:
            # handle reaching the end of tokens gracefully by returning EOF
            return Token(TokenType.EOF, 0, 0, 0, 0, 0, 0)

    def emit(self, token_type: TokenType, text: str) -> None:
        """Appends text to the output."""
        logger.debug("Emitting %s token with text=%r", token_type.name, text)
        self.output_strs.append(FormattedTokenOutput(token_type, text))
        self.update_line_length(text)

    def emit_indent(self) -> None:
        """Emits indentation based on the current indent level."""
        logger.debug(
            "Emitting indentation: indent_level=%d, use_tabs=%s",
            self.indent_level,
            self.config.use_tabs,
        )
        if self.config.use_tabs:
            self.emit(TokenType.WHITESPACE, "\t" * self.indent_level)
        else:
            self.emit(
                TokenType.WHITESPACE,
                " " * self.indent_level * self.config.tab_display_size,
            )

    def format_tokens(self) -> List[FormattedTokenOutput]:
        """Formats the tokens and returns a list of formatted tokens."""
        while self.current_token_index < len(self.tokens):
            token = self.consume_token()  # get the next token
            token_text = self.token_text(token)
            logger.debug(
                "Formatting token at index=%d: %s, indent_level=%d",
                self.current_token_index - 1,
                self.describe_token(token),
                self.indent_level,
            )

            if token.type == TokenType.WHITESPACE:
                # if the whitespace contains a newline then we need to check what
                # the next token is. If the next token is a token that causes a dedent,
                # we need to reduce the indent level PRIOR to emitting this dedent
                # causing token. If we did not do this, the dedent token would be
                # indented cause the following newline to emit the indent at the
                # current level. For example:
                #    {
                #        '\n' causes indent emit here
                #    }  <- this closing brace would be indented incorrectly
                # Handle multiple newlines by only emitting one and ignoring the rest.
                # This causes some loss of fidelity but keeps things simple for now.
                # Block comments containing multiple newlines will be preserved while
                # formatting.
                if "\n" in token_text:
                    next_token = self.peek_token()
                    logger.debug(
                        "Whitespace contains newline. Next token is %s",
                        self.describe_token(next_token),
                    )
                    if self.config.brace_style == "kr" and self.is_opening_brace(
                        next_token
                    ):
                        logger.debug(
                            "Applying K&R brace style before token %s",
                            self.describe_token(next_token),
                        )
                        self.emit(TokenType.WHITESPACE, " ")
                    else:
                        self.emit_line_break(next_token)
                else:
                    next_token = self.next_non_whitespace_token()
                    logger.debug(
                        "Whitespace contains no newline. Next non-whitespace token is %s",
                        self.describe_token(next_token),
                    )
                    if self.config.brace_style == "allman" and self.is_opening_brace(
                        next_token
                    ):
                        logger.debug(
                            "Applying Allman brace style before token %s",
                            self.describe_token(next_token),
                        )
                        self.emit_line_break(next_token)
                    elif self.should_wrap_before(next_token):
                        logger.debug(
                            "Wrapping line before token %s",
                            self.describe_token(next_token),
                        )
                        self.emit_line_break(next_token)
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
                if not self.config.indent_section_blocks:
                    self.emit(TokenType.IDENT, token_text)
                    continue

                offset = 1
                # Find the next non-whitespace token
                next_token = self.peek_token(offset)
                while next_token and next_token.type == TokenType.WHITESPACE:
                    offset += 1
                    next_token = self.peek_token(offset)

                if next_token and next_token.type == TokenType.IDENT:
                    next_text = self.token_text(next_token)

                    if token_text.lower() == "begin":
                        previous_indent = self.indent_level
                        self.emit(TokenType.IDENT, token_text + " " + next_text)
                        # Consume all tokens up to and including the second IDENT
                        for _ in range(offset):
                            self.consume_token()
                        self.consume_token()  # consume the second IDENT itself
                        self.indent_level += 1
                        logger.debug(
                            "Section begin increased indent: %d -> %d",
                            previous_indent,
                            self.indent_level,
                        )
                        continue

                    elif token_text.lower() == "end":
                        if not self.dedent_accounted_for:
                            previous_indent = self.indent_level
                            self.indent_level = max(0, self.indent_level - 1)
                            logger.debug(
                                "Section end reduced indent: %d -> %d",
                                previous_indent,
                                self.indent_level,
                            )
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
                    previous_indent = self.indent_level
                    self.emit(
                        TokenType.PUNCTUATOR, token_text
                    )  # emit this token before updating indentation
                    self.indent_level += 1
                    logger.debug(
                        "Opening punctuator increased indent: %d -> %d",
                        previous_indent,
                        self.indent_level,
                    )
                elif token_text in ["}", "]", ")"]:
                    if not self.dedent_accounted_for:
                        previous_indent = self.indent_level
                        self.indent_level = max(0, self.indent_level - 1)
                        logger.debug(
                            "Closing punctuator reduced indent: %d -> %d",
                            previous_indent,
                            self.indent_level,
                        )
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
