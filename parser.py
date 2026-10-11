from tokens import TokenType


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        return self.tokens[self.position]

    def peek(self, offset=1):
        index = self.position + offset

        if index >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[index]

    def advance(self):
        token = self.current()
        self.position += 1
        return token

    def check(self, token_type):
        return self.current().type == token_type

    def match(self, token_type):
        if self.check(token_type):
            return self.advance()

        return None

    def consume(self, token_type, message):
        if not self.check(token_type):
            token = self.current()

            raise SyntaxError(
                f"EHX Error: {message} "
                f"at line {token.line}, "
                f"column {token.column}"
            )

        return self.advance()

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            pass

    def parse(self):
        statements = []

        self.skip_newlines()

        while not self.check(TokenType.EOF):
            if self.check(TokenType.DEDENT):
                raise SyntaxError(
                    f"EHX Error: unexpected indentation "
                    f"at line {self.current().line}"
                )

            statement = self.parse_statement()
            statements.append(statement)

            if self.check(TokenType.NEWLINE):
                self.skip_newlines()

            elif statement["type"] in ("when", "while", "for", "for_range", "for_in", "fn", "try"):
                self.skip_newlines()

            elif not self.check(TokenType.EOF):
                token = self.current()

                raise SyntaxError(
                    f"EHX Error: expected new line "
                    f"at line {token.line}"
                )

        return {
            "type": "program",
            "statements": statements,
        }

    def parse_statement(self):

        if self.match(TokenType.LET) or self.match(TokenType.SET):
            return self.parse_let()

        if self.match(TokenType.SHOW):
            return self.parse_show()

        if self.match(TokenType.WHEN):
            return self.parse_when()

        if self.match(TokenType.WHILE):
            return self.parse_while()

        if self.match(TokenType.FOR):
            return self.parse_for()

        if self.match(TokenType.FN):
            return self.parse_fn()

        if self.match(TokenType.RETURN):
            return self.parse_return()

        if self.match(TokenType.IMPORT) or self.match(TokenType.LOAD):
            return self.parse_import()

        if self.match(TokenType.TRY):
            return self.parse_try()

        if self.match(TokenType.BREAK):
            return {"type": "break"}

        if self.match(TokenType.CONTINUE):
            return {"type": "continue"}

        if self.check(TokenType.IDENTIFIER):
            # Check if this is an assignment or compound assignment statement
            # Look ahead to see if an assignment operator follows the target
            saved_pos = self.position
            try:
                expr = self.parse_postfix()
                assign_ops = {
                    TokenType.EQUAL: None,
                    TokenType.PLUS_EQUAL: "+",
                    TokenType.MINUS_EQUAL: "-",
                    TokenType.STAR_EQUAL: "*",
                    TokenType.SLASH_EQUAL: "/",
                    TokenType.PERCENT_EQUAL: "%",
                }
                for tok_type, op in assign_ops.items():
                    if self.match(tok_type):
                        rhs = self.parse_expression()
                        if op is not None:
                            val = {
                                "type": "binary",
                                "operator": op,
                                "left": expr,
                                "right": rhs,
                            }
                        else:
                            val = rhs

                        if expr["type"] == "index":
                            return {
                                "type": "index_assign",
                                "target": expr["target"],
                                "index": expr["index"],
                                "value": val,
                            }
                        elif expr["type"] == "variable":
                            return {
                                "type": "assign",
                                "name": expr["name"],
                                "value": val,
                            }
                        raise SyntaxError(
                            f"EHX Error: invalid assignment target at line {self.current().line}"
                        )
            except SyntaxError:
                # If postfix parsing failed, restore position and fall through to full expression
                self.position = saved_pos
            else:
                # Not an assignment; rewind so parse_expression can parse the entire expression (e.g. y * 3)
                self.position = saved_pos

        # Any expression can be an expression statement
        expr = self.parse_expression()
        return {
            "type": "expression_statement",
            "expression": expr,
        }

        token = self.current()

        raise SyntaxError(
            f"EHX Error: unexpected token "
            f"'{token.value}' at line {token.line}"
        )

    def parse_let(self):
        name = self.consume(
            TokenType.IDENTIFIER,
            "expected variable name after declaration ('set' or 'let')",
        )

        self.consume(
            TokenType.EQUAL,
            "expected '=' after variable name",
        )

        value = self.parse_expression()

        return {
            "type": "let",
            "name": name.value,
            "value": value,
        }

    def parse_show(self):
        self.consume(
            TokenType.LEFT_PAREN,
            "expected '(' after 'show'",
        )

        arguments = []

        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.parse_expression())

            while self.match(TokenType.COMMA):
                arguments.append(self.parse_expression())

        self.consume(
            TokenType.RIGHT_PAREN,
            "expected ')' after 'show' arguments",
        )

        return {
            "type": "show",
            "arguments": arguments,
        }

    def parse_when(self):
        branches = []

        condition = self.parse_expression()

        body = self.parse_block()

        branches.append({
            "condition": condition,
            "body": body,
        })

        otherwise = None

        self.skip_newlines()

        # or when
        while (
            self.check(TokenType.OR)
            and self.peek().type == TokenType.WHEN
        ):
            self.advance()  # or
            self.advance()  # when

            condition = self.parse_expression()

            body = self.parse_block()

            branches.append({
                "condition": condition,
                "body": body,
            })

            self.skip_newlines()

        # otherwise
        if self.match(TokenType.OTHERWISE):
            otherwise = self.parse_block()

        return {
            "type": "when",
            "branches": branches,
            "otherwise": otherwise,
        }

    def parse_while(self):
        condition = self.parse_expression()

        body = self.parse_block()

        return {
            "type": "while",
            "condition": condition,
            "body": body,
        }

    def parse_for(self):
        variable = self.consume(
            TokenType.IDENTIFIER,
            "expected variable name after 'for'",
        )

        self.consume(
            TokenType.IN,
            "expected 'in' after for variable",
        )

        first_expr = self.parse_expression()

        if self.match(TokenType.DOT_DOT):
            end = self.parse_expression()
            body = self.parse_block()

            return {
                "type": "for_range",
                "variable": variable.value,
                "start": first_expr,
                "end": end,
                "body": body,
            }

        body = self.parse_block()

        return {
            "type": "for_in",
            "variable": variable.value,
            "iterable": first_expr,
            "body": body,
        }

    def parse_fn(self):
        name = self.consume(
            TokenType.IDENTIFIER,
            "expected function name after 'fn'",
        )

        self.consume(
            TokenType.LEFT_PAREN,
            "expected '(' after function name",
        )

        parameters = []

        if not self.check(TokenType.RIGHT_PAREN):
            param = self.consume(
                TokenType.IDENTIFIER,
                "expected parameter name",
            )
            parameters.append(param.value)

            while self.match(TokenType.COMMA):
                param = self.consume(
                    TokenType.IDENTIFIER,
                    "expected parameter name after ','",
                )
                parameters.append(param.value)

        self.consume(
            TokenType.RIGHT_PAREN,
            "expected ')' after parameter list",
        )

        body = self.parse_block()

        return {
            "type": "fn",
            "name": name.value,
            "parameters": parameters,
            "body": body,
        }

    def parse_return(self):
        if (
            self.check(TokenType.NEWLINE)
            or self.check(TokenType.DEDENT)
            or self.check(TokenType.EOF)
        ):
            return {
                "type": "return",
                "value": None,
            }

        value = self.parse_expression()

        return {
            "type": "return",
            "value": value,
        }

    def parse_import(self):
        path_token = self.consume(
            TokenType.STRING,
            "expected file path string after 'load' or 'import'",
        )

        return {
            "type": "import",
            "path": path_token.value,
        }

    def parse_try(self):
        try_body = self.parse_block()
        self.skip_newlines()

        self.consume(
            TokenType.CATCH,
            "expected 'catch' after 'try' block",
        )

        error_var = None
        if self.check(TokenType.IDENTIFIER):
            error_var = self.advance().value

        catch_body = self.parse_block()

        return {
            "type": "try",
            "try_body": try_body,
            "error_var": error_var,
            "catch_body": catch_body,
        }

    def parse_block(self):
        self.consume(
            TokenType.COLON,
            "expected ':' after block condition",
        )

        self.consume(
            TokenType.NEWLINE,
            "expected new line after ':'",
        )

        self.consume(
            TokenType.INDENT,
            "expected an indented block",
        )

        statements = []

        self.skip_newlines()

        while not self.check(TokenType.DEDENT):
            if self.check(TokenType.EOF):
                raise SyntaxError(
                    "EHX Error: expected end of indented block"
                )

            statement = self.parse_statement()
            statements.append(statement)

            if self.check(TokenType.NEWLINE):
                self.skip_newlines()

            elif statement["type"] in ("when", "while", "for", "for_range", "for_in", "fn", "try"):
                self.skip_newlines()

            elif not self.check(TokenType.DEDENT):
                token = self.current()

                raise SyntaxError(
                    f"EHX Error: expected new line "
                    f"at line {token.line}"
                )

        self.consume(
            TokenType.DEDENT,
            "expected end of block",
        )

        return statements

    # -------------------------
    # Expressions
    # -------------------------

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        expression = self.parse_and()

        while self.match(TokenType.OR):
            right = self.parse_and()

            expression = {
                "type": "binary",
                "operator": "or",
                "left": expression,
                "right": right,
            }

        return expression

    def parse_and(self):
        expression = self.parse_comparison()

        while self.match(TokenType.AND):
            right = self.parse_comparison()

            expression = {
                "type": "binary",
                "operator": "and",
                "left": expression,
                "right": right,
            }

        return expression

    def parse_comparison(self):
        expression = self.parse_term()

        operators = {
            TokenType.EQUAL_EQUAL: "==",
            TokenType.NOT_EQUAL: "!=",
            TokenType.GREATER: ">",
            TokenType.LESS: "<",
            TokenType.GREATER_EQUAL: ">=",
            TokenType.LESS_EQUAL: "<=",
        }

        while self.current().type in operators:
            operator = operators[
                self.advance().type
            ]

            right = self.parse_term()

            expression = {
                "type": "binary",
                "operator": operator,
                "left": expression,
                "right": right,
            }

        return expression

    def parse_term(self):
        expression = self.parse_factor()

        while self.current().type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator_token = self.advance()

            operator = (
                "+"
                if operator_token.type == TokenType.PLUS
                else "-"
            )

            right = self.parse_factor()

            expression = {
                "type": "binary",
                "operator": operator,
                "left": expression,
                "right": right,
            }

        return expression

    def parse_factor(self):
        expression = self.parse_power()

        while self.current().type in (
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.SLASH_SLASH,
            TokenType.PERCENT,
        ):
            operator_token = self.advance()

            if operator_token.type == TokenType.STAR:
                operator = "*"
            elif operator_token.type == TokenType.SLASH:
                operator = "/"
            elif operator_token.type == TokenType.SLASH_SLASH:
                operator = "//"
            else:
                operator = "%"

            right = self.parse_power()

            expression = {
                "type": "binary",
                "operator": operator,
                "left": expression,
                "right": right,
            }

        return expression

    def parse_power(self):
        expression = self.parse_unary()

        if self.match(TokenType.STAR_STAR):
            # Exponentiation is right-associative (2 ** 3 ** 2 == 2 ** (3 ** 2))
            right = self.parse_power()
            return {
                "type": "binary",
                "operator": "**",
                "left": expression,
                "right": right,
            }

        return expression

    def parse_unary(self):
        if self.match(TokenType.MINUS):
            return {
                "type": "unary",
                "operator": "-",
                "value": self.parse_unary(),
            }

        if self.match(TokenType.NOT):
            return {
                "type": "unary",
                "operator": "not",
                "value": self.parse_unary(),
            }

        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()

        while True:
            if self.match(TokenType.LEFT_BRACKET):
                index = self.parse_expression()
                self.consume(
                    TokenType.RIGHT_BRACKET,
                    "expected ']' after index",
                )
                expr = {
                    "type": "index",
                    "target": expr,
                    "index": index,
                }

            elif self.match(TokenType.DOT):
                member = self.consume(
                    TokenType.IDENTIFIER,
                    "expected member name after '.'",
                )
                if self.match(TokenType.LEFT_PAREN):
                    arguments = []
                    if not self.check(TokenType.RIGHT_PAREN):
                        arguments.append(self.parse_expression())
                        while self.match(TokenType.COMMA):
                            arguments.append(self.parse_expression())
                    self.consume(
                        TokenType.RIGHT_PAREN,
                        "expected ')' after method arguments",
                    )
                    expr = {
                        "type": "method_call",
                        "target": expr,
                        "method": member.value,
                        "arguments": arguments,
                    }
                else:
                    expr = {
                        "type": "member",
                        "target": expr,
                        "name": member.value,
                    }

            elif self.match(TokenType.LEFT_PAREN):
                arguments = []
                if not self.check(TokenType.RIGHT_PAREN):
                    arguments.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        arguments.append(self.parse_expression())
                self.consume(
                    TokenType.RIGHT_PAREN,
                    "expected ')' after arguments",
                )

                if expr["type"] == "variable":
                    expr = {
                        "type": "call",
                        "name": expr["name"],
                        "arguments": arguments,
                    }
                else:
                    expr = {
                        "type": "call_expr",
                        "callee": expr,
                        "arguments": arguments,
                    }
            else:
                break

        return expr

    def parse_primary(self):

        if self.match(TokenType.TRUE):
            return {
                "type": "literal",
                "value": True,
            }

        if self.match(TokenType.FALSE):
            return {
                "type": "literal",
                "value": False,
            }

        if self.match(TokenType.NONE):
            return {
                "type": "literal",
                "value": None,
            }

        if self.check(TokenType.NUMBER):
            return {
                "type": "literal",
                "value": self.advance().value,
            }

        if self.check(TokenType.STRING):
            return {
                "type": "literal",
                "value": self.advance().value,
            }

        if self.check(TokenType.FSTRING):
            token = self.advance()
            raw_parts = token.value
            parsed_parts = []
            from lexer import Lexer
            for part in raw_parts:
                if part["type"] == "literal":
                    parsed_parts.append({
                        "type": "literal",
                        "value": part["value"],
                    })
                else:
                    expr_tokens = Lexer(part["source"]).tokenize()
                    clean_tokens = [t for t in expr_tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
                    if not clean_tokens:
                        raise SyntaxError(f"EHX Error: empty expression in f-string at line {token.line}")
                    from tokens import Token
                    clean_tokens.append(Token(TokenType.EOF, "", token.line, token.column))
                    sub_parser = Parser(clean_tokens)
                    expr_ast = sub_parser.parse_expression()
                    parsed_parts.append({
                        "type": "expr",
                        "expression": expr_ast,
                    })
            return {
                "type": "fstring",
                "parts": parsed_parts,
            }

        if self.check(TokenType.IDENTIFIER):
            return {
                "type": "variable",
                "name": self.advance().value,
            }

        # List literal: [item1, item2, ...]
        if self.match(TokenType.LEFT_BRACKET):
            items = []
            if not self.check(TokenType.RIGHT_BRACKET):
                items.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RIGHT_BRACKET):
                        break
                    items.append(self.parse_expression())
            self.consume(
                TokenType.RIGHT_BRACKET,
                "expected ']' after list items",
            )
            return {
                "type": "list",
                "items": items,
            }

        # Dict literal: {key1: val1, key2: val2, ...}
        if self.match(TokenType.LEFT_BRACE):
            entries = []
            if not self.check(TokenType.RIGHT_BRACE):
                key = self.parse_expression()
                self.consume(
                    TokenType.COLON,
                    "expected ':' after dictionary key",
                )
                val = self.parse_expression()
                entries.append({"key": key, "value": val})

                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RIGHT_BRACE):
                        break
                    key = self.parse_expression()
                    self.consume(
                        TokenType.COLON,
                        "expected ':' after dictionary key",
                    )
                    val = self.parse_expression()
                    entries.append({"key": key, "value": val})

            self.consume(
                TokenType.RIGHT_BRACE,
                "expected '}' after dictionary entries",
            )
            return {
                "type": "dict",
                "entries": entries,
            }

        if self.match(TokenType.LEFT_PAREN):
            expression = self.parse_expression()

            self.consume(
                TokenType.RIGHT_PAREN,
                "expected ')'",
            )

            return expression

        token = self.current()

        raise SyntaxError(
            f"EHX Error: expected expression "
            f"at line {token.line}"
        )