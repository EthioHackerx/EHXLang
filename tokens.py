from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    LET = auto()
    SET = auto()
    SHOW = auto()

    WHEN = auto()
    OTHERWISE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    FN = auto()
    RETURN = auto()
    IMPORT = auto()
    LOAD = auto()
    TRY = auto()
    CATCH = auto()
    BREAK = auto()
    CONTINUE = auto()
    NONE = auto()

    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Values
    IDENTIFIER = auto()
    STRING = auto()
    FSTRING = auto()
    NUMBER = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    STAR_STAR = auto()       # ** (power / exponent)
    SLASH_SLASH = auto()     # // (integer floor division)

    EQUAL = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    STAR_EQUAL = auto()
    SLASH_EQUAL = auto()
    PERCENT_EQUAL = auto()   # %=
    EQUAL_EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQUAL = auto()
    LESS_EQUAL = auto()

    DOT_DOT = auto()

    # Symbols
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()

    # Indentation / structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()

    # Special
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    column: int