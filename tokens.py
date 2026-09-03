from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    SET = auto()
    SAY = auto()

    # Values
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQUAL = auto()

    # Symbols
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()

    # Special
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    column: int