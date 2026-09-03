from tokens import Token, TokenType


class Lexer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self):
        tokens = []

        while not self.is_at_end():
            current = self.peek()

            # Spaces and tabs
            if current in " \t\r":
                self.advance()
                continue

            # New line
            if current == "\n":
                tokens.append(
                    Token(
                        TokenType.NEWLINE,
                        "\n",
                        self.line,
                        self.column
                    )
                )

                self.advance()
                self.line += 1
                self.column = 1
                continue

            # Comments
            if current == "#":
                self.skip_comment()
                continue

            # Strings
            if current == '"':
                tokens.append(self.read_string())
                continue

            # Numbers
            if current.isdigit():
                tokens.append(self.read_number())
                continue

            # Identifiers / keywords
            if current.isalpha() or current == "_":
                tokens.append(self.read_identifier())
                continue

            # Two-character operators
            if current == "=" and self.peek_next() == "=":
                tokens.append(
                    Token(
                        TokenType.EQUAL_EQUAL,
                        "==",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                self.advance()
                continue

            if current == "!" and self.peek_next() == "=":
                tokens.append(
                    Token(
                        TokenType.NOT_EQUAL,
                        "!=",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                self.advance()
                continue

            if current == ">" and self.peek_next() == "=":
                tokens.append(
                    Token(
                        TokenType.GREATER_EQUAL,
                        ">=",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                self.advance()
                continue

            if current == "<" and self.peek_next() == "=":
                tokens.append(
                    Token(
                        TokenType.LESS_EQUAL,
                        "<=",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                self.advance()
                continue

            # Single-character operators
            if current == "+":
                tokens.append(
                    Token(
                        TokenType.PLUS,
                        "+",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == "-":
                tokens.append(
                    Token(
                        TokenType.MINUS,
                        "-",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == "*":
                tokens.append(
                    Token(
                        TokenType.STAR,
                        "*",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == "/":
                tokens.append(
                    Token(
                        TokenType.SLASH,
                        "/",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == "=":
                tokens.append(
                    Token(
                        TokenType.EQUAL,
                        "=",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == ">":
                tokens.append(
                    Token(
                        TokenType.GREATER,
                        ">",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == "<":
                tokens.append(
                    Token(
                        TokenType.LESS,
                        "<",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            # Parentheses
            if current == "(":
                tokens.append(
                    Token(
                        TokenType.LEFT_PAREN,
                        "(",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            if current == ")":
                tokens.append(
                    Token(
                        TokenType.RIGHT_PAREN,
                        ")",
                        self.line,
                        self.column
                    )
                )
                self.advance()
                continue

            # Unknown character
            raise SyntaxError(
                f"EHX Error: unexpected character "
                f"'{current}' on line {self.line}"
            )

        tokens.append(
            Token(
                TokenType.EOF,
                None,
                self.line,
                self.column
            )
        )

        return tokens

    # -------------------------
    # Character utilities
    # -------------------------

    def peek(self):
        return self.source[self.position]

    def peek_next(self):
        if self.position + 1 >= len(self.source):
            return "\0"

        return self.source[self.position + 1]

    def advance(self):
        self.position += 1
        self.column += 1

    def is_at_end(self):
        return self.position >= len(self.source)

    # -------------------------
    # Comments
    # -------------------------

    def skip_comment(self):
        while not self.is_at_end() and self.peek() != "\n":
            self.advance()

    # -------------------------
    # Strings
    # -------------------------

    def read_string(self):
        start_line = self.line
        start_column = self.column

        self.advance()

        value = ""

        while not self.is_at_end() and self.peek() != '"':
            if self.peek() == "\n":
                raise SyntaxError(
                    f"EHX Error: unterminated string "
                    f"on line {start_line}"
                )

            value += self.peek()
            self.advance()

        if self.is_at_end():
            raise SyntaxError(
                f"EHX Error: unterminated string "
                f"on line {start_line}"
            )

        self.advance()

        return Token(
            TokenType.STRING,
            value,
            start_line,
            start_column
        )

    # -------------------------
    # Numbers
    # -------------------------

    def read_number(self):
        start_line = self.line
        start_column = self.column

        value = ""

        while not self.is_at_end() and self.peek().isdigit():
            value += self.peek()
            self.advance()

        # Decimal number
        if (
            not self.is_at_end()
            and self.peek() == "."
            and self.position + 1 < len(self.source)
            and self.source[self.position + 1].isdigit()
        ):
            value += "."
            self.advance()

            while not self.is_at_end() and self.peek().isdigit():
                value += self.peek()
                self.advance()

            number = float(value)

        else:
            number = int(value)

        return Token(
            TokenType.NUMBER,
            number,
            start_line,
            start_column
        )

    # -------------------------
    # Identifiers / Keywords
    # -------------------------

    def read_identifier(self):
        start_line = self.line
        start_column = self.column

        value = ""

        while (
            not self.is_at_end()
            and (
                self.peek().isalnum()
                or self.peek() == "_"
            )
        ):
            value += self.peek()
            self.advance()

        keywords = {
            "set": TokenType.SET,
            "say": TokenType.SAY,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "not": TokenType.NOT
        }

        token_type = keywords.get(
            value,
            TokenType.IDENTIFIER
        )

        return Token(
            token_type,
            value,
            start_line,
            start_column
        )