from tokens import Token, TokenType


class Lexer:
    KEYWORDS = {
        "let": TokenType.LET,
        "set": TokenType.SET,
        "show": TokenType.SHOW,
        "when": TokenType.WHEN,
        "otherwise": TokenType.OTHERWISE,
        "while": TokenType.WHILE,
        "for": TokenType.FOR,
        "in": TokenType.IN,
        "fn": TokenType.FN,
        "return": TokenType.RETURN,
        "import": TokenType.IMPORT,
        "load": TokenType.LOAD,
        "try": TokenType.TRY,
        "catch": TokenType.CATCH,
        "break": TokenType.BREAK,
        "continue": TokenType.CONTINUE,
        "none": TokenType.NONE,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
    }

    def __init__(self, source):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.position = 0
        self.line = 1
        self.column = 1

        self.tokens = []

        # Indentation levels.
        # Level 0 = no indentation.
        self.indents = [0]

        self.at_line_start = True
        self.bracket_depth = 0

    def current(self):
        if self.position >= len(self.source):
            return "\0"

        return self.source[self.position]

    def peek(self):
        if self.position + 1 >= len(self.source):
            return "\0"

        return self.source[self.position + 1]

    def advance(self):
        char = self.current()

        if char == "\n":
            self.position += 1
            self.line += 1
            self.column = 1
            self.at_line_start = True
        else:
            self.position += 1
            self.column += 1
            self.at_line_start = False

        return char

    def add_token(self, token_type, value, line=None, column=None):
        self.tokens.append(
            Token(
                token_type,
                value,
                line if line is not None else self.line,
                column if column is not None else self.column,
            )
        )

    def handle_indentation(self):
        # Inside brackets/parentheses/braces, indentation is ignored (implicit line continuation)
        if self.bracket_depth > 0:
            while self.current() == " ":
                self.advance()
            self.at_line_start = False
            return

        start_line = self.line
        start_column = self.column

        spaces = 0

        while self.current() == " ":
            spaces += 1
            self.advance()

        # Tabs are intentionally not supported.
        if self.current() == "\t":
            raise SyntaxError(
                f"EHX Error: tabs are not allowed for indentation "
                f"at line {self.line}"
            )

        # Blank line or end of file
        if self.current() in ("\n", "\0"):
            if self.current() == "\n":
                self.advance()
            return

        # Comment-only line
        if self.current() == "#":
            while self.current() not in ("\n", "\0"):
                self.advance()

            if self.current() == "\n":
                self.advance()

            return

        current_indent = self.indents[-1]

        if spaces > current_indent:
            self.indents.append(spaces)

            self.add_token(
                TokenType.INDENT,
                spaces,
                start_line,
                start_column,
            )

        elif spaces < current_indent:
            while spaces < self.indents[-1]:
                self.indents.pop()

                self.add_token(
                    TokenType.DEDENT,
                    spaces,
                    start_line,
                    start_column,
                )

            if spaces != self.indents[-1]:
                raise SyntaxError(
                    f"EHX Error: inconsistent indentation "
                    f"at line {self.line}"
                )

        self.at_line_start = False

    def read_number(self):
        start_line = self.line
        start_column = self.column

        number = ""

        while self.current().isdigit():
            number += self.advance()

        # Decimal number
        if self.current() == "." and self.peek() != ".":
            number += self.advance()

            while self.current().isdigit():
                number += self.advance()

            value = float(number)
        else:
            value = int(number)

        self.add_token(
            TokenType.NUMBER,
            value,
            start_line,
            start_column,
        )

    def read_identifier(self):
        start_line = self.line
        start_column = self.column

        identifier = ""

        while (
            self.current().isalnum()
            or self.current() == "_"
        ):
            identifier += self.advance()

        token_type = self.KEYWORDS.get(
            identifier,
            TokenType.IDENTIFIER,
        )

        value = identifier

        if token_type == TokenType.TRUE:
            value = True

        elif token_type == TokenType.FALSE:
            value = False

        self.add_token(
            token_type,
            value,
            start_line,
            start_column,
        )

    def read_string(self, quote_char='"'):
        start_line = self.line
        start_column = self.column

        self.advance()  # opening quote

        value = ""

        while self.current() not in (quote_char, "\0"):
            if self.current() == "\\":
                self.advance()

                escaped = self.current()

                if escaped == "n":
                    value += "\n"
                elif escaped == "t":
                    value += "\t"
                elif escaped == quote_char:
                    value += quote_char
                elif escaped == "\\":
                    value += "\\"
                else:
                    value += escaped

                self.advance()

            else:
                value += self.advance()

        if self.current() == "\0":
            raise SyntaxError(
                f"EHX Error: unterminated string "
                f"at line {start_line}"
            )

        self.advance()  # closing quote

        self.add_token(
            TokenType.STRING,
            value,
            start_line,
            start_column,
        )

    def read_fstring(self, quote_char='"'):
        start_line = self.line
        start_column = self.column

        self.advance()  # skip 'f' or 'F'
        self.advance()  # opening quote

        raw_parts = []
        current_literal = ""

        while self.current() not in (quote_char, "\0"):
            if self.current() == "\\":
                self.advance()
                escaped = self.current()
                if escaped == "n":
                    current_literal += "\n"
                elif escaped == "t":
                    current_literal += "\t"
                elif escaped == quote_char:
                    current_literal += quote_char
                elif escaped == "\\":
                    current_literal += "\\"
                elif escaped in ("{", "}"):
                    current_literal += escaped
                else:
                    current_literal += escaped
                self.advance()
            elif self.current() == "{" and self.peek() == "{":
                # Escaped {{ -> literal {
                current_literal += "{"
                self.advance()
                self.advance()
            elif self.current() == "}" and self.peek() == "}":
                # Escaped }} -> literal }
                current_literal += "}"
                self.advance()
                self.advance()
            elif self.current() == "{":
                if current_literal:
                    raw_parts.append({"type": "literal", "value": current_literal})
                    current_literal = ""
                self.advance()  # skip '{'
                expr_src = ""
                brace_depth = 1
                while self.current() != "\0" and brace_depth > 0:
                    if self.current() == "{":
                        brace_depth += 1
                        expr_src += self.advance()
                    elif self.current() == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            self.advance()  # skip closing '}'
                            break
                        else:
                            expr_src += self.advance()
                    elif self.current() in ('"', "'"):
                        # Handle quoted strings inside { ... }
                        inner_quote = self.advance()
                        expr_src += inner_quote
                        while self.current() not in (inner_quote, "\0"):
                            if self.current() == "\\":
                                expr_src += self.advance()
                            if self.current() != "\0":
                                expr_src += self.advance()
                        if self.current() == inner_quote:
                            expr_src += self.advance()
                    else:
                        expr_src += self.advance()

                if brace_depth > 0:
                    raise SyntaxError(f"EHX Error: unclosed '{{' in f-string at line {start_line}")

                raw_parts.append({"type": "expr", "source": expr_src.strip()})
            else:
                current_literal += self.advance()

        if self.current() == "\0":
            raise SyntaxError(
                f"EHX Error: unterminated f-string at line {start_line}"
            )

        self.advance()  # closing quote

        if current_literal:
            raw_parts.append({"type": "literal", "value": current_literal})

        self.add_token(
            TokenType.FSTRING,
            raw_parts,
            start_line,
            start_column,
        )

    def tokenize(self):
        while self.position < len(self.source):

            if self.at_line_start:
                self.handle_indentation()

                if self.at_line_start:
                    continue

            if self.position >= len(self.source):
                break

            char = self.current()

            # Spaces inside a line
            if char == " ":
                self.advance()
                continue

            # Newline
            if char == "\n":
                if self.bracket_depth == 0:
                    self.add_token(
                        TokenType.NEWLINE,
                        "\n",
                    )
                self.advance()
                continue

            # Comments
            if char == "#":
                while self.current() not in ("\n", "\0"):
                    self.advance()

                continue

            # Numbers
            if char.isdigit():
                self.read_number()
                continue

            # f-strings: f"..." or f'...'
            if char in ('f', 'F') and self.peek() in ('"', "'"):
                self.read_fstring(self.peek())
                continue

            # Identifiers / keywords
            if char.isalpha() or char == "_":
                self.read_identifier()
                continue

            # Strings (double and single quotes)
            if char in ('"', "'"):
                self.read_string(char)
                continue

            # Two-character operators

            if char == "=" and self.peek() == "=":
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                self.add_token(
                    TokenType.EQUAL_EQUAL,
                    "==",
                    line,
                    column,
                )
                continue

            if char == "!" and self.peek() == "=":
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                self.add_token(
                    TokenType.NOT_EQUAL,
                    "!=",
                    line,
                    column,
                )
                continue

            if char == ">" and self.peek() == "=":
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                self.add_token(
                    TokenType.GREATER_EQUAL,
                    ">=",
                    line,
                    column,
                )
                continue

            if char == "<" and self.peek() == "=":
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                self.add_token(
                    TokenType.LESS_EQUAL,
                    "<=",
                    line,
                    column,
                )
                continue

            if char == "+" and self.peek() == "=":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.PLUS_EQUAL, "+=", line, column)
                continue

            if char == "-" and self.peek() == "=":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.MINUS_EQUAL, "-=", line, column)
                continue

            if char == "*" and self.peek() == "*":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.STAR_STAR, "**", line, column)
                continue

            if char == "*" and self.peek() == "=":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.STAR_EQUAL, "*=", line, column)
                continue

            if char == "/" and self.peek() == "/":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.SLASH_SLASH, "//", line, column)
                continue

            if char == "/" and self.peek() == "=":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.SLASH_EQUAL, "/=", line, column)
                continue

            if char == "%" and self.peek() == "=":
                line, column = self.line, self.column
                self.advance()
                self.advance()
                self.add_token(TokenType.PERCENT_EQUAL, "%=", line, column)
                continue

            if char == "." and self.peek() == ".":
                line = self.line
                column = self.column

                self.advance()
                self.advance()

                self.add_token(
                    TokenType.DOT_DOT,
                    "..",
                    line,
                    column,
                )
                continue

            # Single-character operators

            single_tokens = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "=": TokenType.EQUAL,
                ">": TokenType.GREATER,
                "<": TokenType.LESS,
                "(": TokenType.LEFT_PAREN,
                ")": TokenType.RIGHT_PAREN,
                "[": TokenType.LEFT_BRACKET,
                "]": TokenType.RIGHT_BRACKET,
                "{": TokenType.LEFT_BRACE,
                "}": TokenType.RIGHT_BRACE,
                ":": TokenType.COLON,
                ",": TokenType.COMMA,
                ".": TokenType.DOT,
            }

            if char in single_tokens:
                line = self.line
                column = self.column

                if char in ("(", "[", "{"):
                    self.bracket_depth += 1
                elif char in (")", "]", "}"):
                    if self.bracket_depth > 0:
                        self.bracket_depth -= 1

                self.advance()

                self.add_token(
                    single_tokens[char],
                    char,
                    line,
                    column,
                )
                continue

            raise SyntaxError(
                f"EHX Error: unexpected character "
                f"'{char}' at line {self.line}, "
                f"column {self.column}"
            )

        # Finish any remaining indentation levels.
        while len(self.indents) > 1:
            self.indents.pop()

            self.add_token(
                TokenType.DEDENT,
                0,
                self.line,
                self.column,
            )

        self.add_token(
            TokenType.EOF,
            None,
            self.line,
            self.column,
        )

        return self.tokens