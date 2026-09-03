from tokens import TokenType


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def parse(self):
        program = []

        while not self.check(TokenType.EOF):
            if self.match(TokenType.NEWLINE):
                continue

            program.append(self.parse_statement())

            if self.check(TokenType.NEWLINE):
                self.advance()

        return program

    # -------------------------
    # Statements
    # -------------------------

    def parse_statement(self):
        if self.match(TokenType.SET):
            return self.parse_set()

        if self.match(TokenType.SAY):
            return self.parse_say()

        token = self.current()

        raise SyntaxError(
            f"EHX Error: unexpected token "
            f"'{token.value}' on line {token.line}"
        )

    def parse_set(self):
        name = self.consume(
            TokenType.IDENTIFIER,
            "expected variable name after 'set'"
        )

        self.consume(
            TokenType.EQUAL,
            "expected '=' after variable name"
        )

        value = self.parse_expression()

        return {
            "type": "set",
            "name": name.value,
            "value": value
        }

    def parse_say(self):
        value = self.parse_expression()

        return {
            "type": "say",
            "value": value
        }

    # -------------------------
    # Expressions
    # -------------------------

    def parse_expression(self):
        return self.parse_or()

    # OR
    def parse_or(self):
        expression = self.parse_and()

        while self.match(TokenType.OR):
            right = self.parse_and()

            expression = {
                "type": "logical",
                "operator": "or",
                "left": expression,
                "right": right
            }

        return expression

    # AND
    def parse_and(self):
        expression = self.parse_comparison()

        while self.match(TokenType.AND):
            right = self.parse_comparison()

            expression = {
                "type": "logical",
                "operator": "and",
                "left": expression,
                "right": right
            }

        return expression

    # Comparisons
    def parse_comparison(self):
        expression = self.parse_addition()

        while (
            self.match(
                TokenType.EQUAL_EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.GREATER,
                TokenType.LESS,
                TokenType.GREATER_EQUAL,
                TokenType.LESS_EQUAL
            )
        ):
            operator = self.previous().value
            right = self.parse_addition()

            expression = {
                "type": "comparison",
                "operator": operator,
                "left": expression,
                "right": right
            }

        return expression

    # Addition / subtraction
    def parse_addition(self):
        expression = self.parse_multiplication()

        while (
            self.match(
                TokenType.PLUS,
                TokenType.MINUS
            )
        ):
            operator = self.previous().value
            right = self.parse_multiplication()

            expression = {
                "type": "binary",
                "operator": operator,
                "left": expression,
                "right": right
            }

        return expression

    # Multiplication / division
    def parse_multiplication(self):
        expression = self.parse_unary()

        while (
            self.match(
                TokenType.STAR,
                TokenType.SLASH
            )
        ):
            operator = self.previous().value
            right = self.parse_unary()

            expression = {
                "type": "binary",
                "operator": operator,
                "left": expression,
                "right": right
            }

        return expression

    # Unary operators
    def parse_unary(self):
        if self.match(TokenType.MINUS):
            return {
                "type": "unary",
                "operator": "-",
                "value": self.parse_unary()
            }

        if self.match(TokenType.NOT):
            return {
                "type": "unary",
                "operator": "not",
                "value": self.parse_unary()
            }

        return self.parse_primary()

    # Primary values
    def parse_primary(self):
        if self.match(TokenType.NUMBER):
            return {
                "type": "number",
                "value": self.previous().value
            }

        if self.match(TokenType.STRING):
            return {
                "type": "string",
                "value": self.previous().value
            }

        if self.match(TokenType.TRUE):
            return {
                "type": "boolean",
                "value": True
            }

        if self.match(TokenType.FALSE):
            return {
                "type": "boolean",
                "value": False
            }

        if self.match(TokenType.IDENTIFIER):
            return {
                "type": "identifier",
                "name": self.previous().value
            }

        if self.match(TokenType.LEFT_PAREN):
            expression = self.parse_expression()

            self.consume(
                TokenType.RIGHT_PAREN,
                "expected ')' after expression"
            )

            return expression

        token = self.current()

        raise SyntaxError(
            f"EHX Error: expected expression "
            f"on line {token.line}"
        )

    # -------------------------
    # Parser utilities
    # -------------------------

    def current(self):
        return self.tokens[self.position]

    def previous(self):
        return self.tokens[self.position - 1]

    def advance(self):
        if not self.check(TokenType.EOF):
            self.position += 1

        return self.previous()

    def check(self, token_type):
        return self.current().type == token_type

    def match(self, *token_types):
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True

        return False

    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()

        token = self.current()

        raise SyntaxError(
            f"EHX Error: {message} "
            f"on line {token.line}"
        )