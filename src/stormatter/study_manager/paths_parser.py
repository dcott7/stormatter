from pathlib import Path
from typing import Dict

from ..parsing import Parser
from ..parsing.token import TokenType


class PathsDatParser(Parser):
    """Parser class for parsing paths.dat file."""

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self.data: Dict[str, Path] = {}

    def parse(self) -> Dict[str, Path]:
        """Parse the paths.dat file and populate the data dictionary."""
        tokens = self.remove_comments_and_whitespace()
        stream = self.token_stream(tokens)

        while not stream.eof():
            name_token = stream.expect(TokenType.IDENT)
            path_token = stream.expect(TokenType.STRING)

            name = name_token.to_byte_slice(self.source)
            raw_path = path_token.to_byte_slice(self.source)
            path_value = self._strip_quotes(raw_path)
            self.data[name] = Path(path_value).resolve()

        return self.data

    @staticmethod
    def _strip_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1]
        return value

    def write(self, path: Path) -> None:
        """Write the current data back to a paths.dat file."""
        lines: list[str] = []
        for name in sorted(self.data.keys()):
            path_value = self.data[name]
            lines.append(f'{name} "{path_value}"')
        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
